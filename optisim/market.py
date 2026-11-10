"""The simulated market: instruments, fair values, matching, accounts, limits, clock."""
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .book import Order, OrderBook
from .types import Instrument, Trade, TradeTick


@dataclass
class Limits:
    position_limit: Optional[int] = None          # |position| per instrument, worst case incl. resting orders
    max_ops_per_sec: Optional[int] = None         # inserts + amends + deletes per rolling sim second
    max_outstanding_volume: Optional[int] = None  # total resting volume per instrument
    self_trade_prevention: bool = True


@dataclass
class Account:
    name: str
    limits: Limits
    position: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cash: float = 0.0
    new_trades: Dict[str, List[Trade]] = field(default_factory=lambda: defaultdict(list))
    trade_history: Dict[str, List[Trade]] = field(default_factory=lambda: defaultdict(list))
    tick_cursor: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ops: deque = field(default_factory=deque)
    n_ops: int = 0
    n_rejects: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    volume_traded: int = 0
    equity_curve: List[Tuple[float, float]] = field(default_factory=list)
    max_abs_delta: int = 0


@dataclass
class Stock:
    name: str
    fv: float
    sigma: float          # stdev of fair value change per step
    jump_prob: float      # per step probability of a news jump
    jump_sigma: float
    history: deque = field(default_factory=lambda: deque(maxlen=2000))


class Market:
    def __init__(self, dt: float = 0.1, seed: int = 0):
        self.dt = dt
        self.t = 0.0
        self.step_no = 0
        self.rng = random.Random(seed)
        self.instruments: Dict[str, Instrument] = {}
        self.books: Dict[str, OrderBook] = {}
        self.stocks: Dict[str, Stock] = {}
        self.accounts: Dict[str, Account] = {}
        self.actors: List = []
        self.ticks: Dict[str, List[TradeTick]] = defaultdict(list)
        self.pauses: List[Tuple[str, float, float]] = []
        self._next_id = 1
        self._seq = 0
        self.sample_every = 10

    # ---------------- setup ----------------
    def add_stock(self, name, fv, sigma, jump_prob=0.0, jump_sigma=0.0):
        s = Stock(name, fv, sigma, jump_prob, jump_sigma)
        s.history.append(fv)
        self.stocks[name] = s

    def add_instrument(self, instrument_id, underlying, tick_size=0.1, is_primary=True):
        self.instruments[instrument_id] = Instrument(instrument_id, tick_size, False, underlying, is_primary)
        self.books[instrument_id] = OrderBook(instrument_id)

    def add_account(self, name, limits: Limits = None) -> Account:
        acc = Account(name, limits or Limits())
        self.accounts[name] = acc
        return acc

    def add_actor(self, actor):
        self.actors.append(actor)

    # ---------------- helpers ----------------
    def tick(self, inst):
        return self.instruments[inst].tick_size

    def to_ticks(self, inst, price):
        return int(round(price / self.tick(inst)))

    def to_price(self, inst, ticks):
        return round(ticks * self.tick(inst), 6)

    def fv(self, inst_or_stock):
        if inst_or_stock in self.stocks:
            return self.stocks[inst_or_stock].fv
        return self.stocks[self.instruments[inst_or_stock].underlying].fv

    def lagged_fv(self, stock, lag_steps):
        h = self.stocks[stock].history
        return h[-1 - lag_steps] if len(h) > lag_steps else h[0]

    def net_delta(self, owner):
        """Net position per underlying stock (primary + dual listings combined)."""
        d = defaultdict(int)
        for inst, pos in self.accounts[owner].position.items():
            d[self.instruments[inst].underlying] += pos
        return dict(d)

    def mid(self, inst):
        b, a = self.books[inst].best("bid"), self.books[inst].best("ask")
        if b is None or a is None:
            return None
        return self.to_price(inst, b + a) / 2

    def resting(self, owner, inst, side=None):
        return [o for o in self.books[inst].orders.values()
                if o.owner == owner and (side is None or o.side == side)]

    # ---------------- rate limit ----------------
    def _charge_op(self, acc: Account) -> bool:
        lim = acc.limits.max_ops_per_sec
        while acc.ops and acc.ops[0] <= self.t - 1.0 + 1e-9:
            acc.ops.popleft()
        if lim is not None and len(acc.ops) >= lim:
            acc.n_rejects["rate_limit"] += 1
            return False
        acc.ops.append(self.t)
        acc.n_ops += 1
        return True

    # ---------------- order entry ----------------
    def submit(self, owner, inst, side, price_ticks, volume, ioc=False, charge=True):
        """Returns (order_id or None, reason). Fills are applied immediately."""
        acc = self.accounts[owner]
        book = self.books[inst]
        if side not in ("bid", "ask"):
            return None, "bad side"
        if volume <= 0 or int(volume) != volume:
            acc.n_rejects["bad_volume"] += 1
            return None, "volume must be a positive integer"
        if self.instruments[inst].paused:
            acc.n_rejects["paused"] += 1
            return None, "instrument paused"
        if charge and not self._charge_op(acc):
            return None, "rate limit exceeded"
        lim = acc.limits
        if lim.position_limit is not None:
            pos = acc.position[inst]
            rest = self.resting(owner, inst, side)
            pending = sum(o.volume for o in rest)
            worst = pos + pending + volume if side == "bid" else pos - pending - volume
            if abs(worst) > lim.position_limit:
                acc.n_rejects["position_limit"] += 1
                return None, "position limit (worst case incl. resting orders)"
        if lim.max_outstanding_volume is not None and not ioc:
            if sum(o.volume for o in self.resting(owner, inst)) + volume > lim.max_outstanding_volume:
                acc.n_rejects["outstanding_limit"] += 1
                return None, "outstanding volume limit"
        if lim.self_trade_prevention and book.own_would_cross(owner, side, price_ticks):
            acc.n_rejects["self_trade"] += 1
            return None, "would self-trade"

        oid = self._next_id
        self._next_id += 1
        fills, remaining = book.match(side, price_ticks, volume)
        for f in fills:
            self._apply_fill(inst, aggressor=owner, aggressor_side=side, aggressor_oid=oid, fill=f)
        if remaining > 0 and not ioc:
            self._seq += 1
            book.add(Order(oid, owner, inst, side, price_ticks, remaining, self._seq))
        return oid, ""

    def _apply_fill(self, inst, aggressor, aggressor_side, aggressor_oid, fill):
        px = self.to_price(inst, fill.price)
        v = fill.volume
        passive = fill.resting.owner
        for name, side, oid in ((aggressor, aggressor_side, aggressor_oid),
                                (passive, fill.resting.side, fill.resting.order_id)):
            acc = self.accounts[name]
            sgn = 1 if side == "bid" else -1
            acc.position[inst] += sgn * v
            acc.cash -= sgn * v * px
            acc.volume_traded += v
            tr = Trade(oid, inst, px, v, side)
            acc.new_trades[inst].append(tr)
            acc.trade_history[inst].append(tr)
        buyer = aggressor if aggressor_side == "bid" else passive
        seller = passive if aggressor_side == "bid" else aggressor
        self.ticks[inst].append(TradeTick(self.t, inst, px, v, aggressor_side, buyer, seller))

    def cancel(self, owner, inst, order_id, charge=True):
        o = self.books[inst].orders.get(order_id)
        if o is None or o.owner != owner:
            return False
        if charge and not self._charge_op(self.accounts[owner]):
            return False
        return self.books[inst].remove(order_id)

    def cancel_all(self, owner, inst, side=None, charge=True):
        """Counts as ONE op (like delete_orders on the real exchange; assumption)."""
        rest = self.resting(owner, inst, side)
        if not rest:
            return 0
        if charge and not self._charge_op(self.accounts[owner]):
            return 0
        for o in rest:
            self.books[inst].remove(o.order_id)
        return len(rest)

    def amend(self, owner, inst, order_id, new_volume, charge=True):
        """Reduce keeps time priority; increase sends you to the back of the queue."""
        o = self.books[inst].orders.get(order_id)
        if o is None or o.owner != owner or new_volume <= 0:
            return False
        if charge and not self._charge_op(self.accounts[owner]):
            return False
        acc = self.accounts[owner]
        if new_volume > o.volume and acc.limits.position_limit is not None:
            pending = sum(x.volume for x in self.resting(owner, inst, o.side)) - o.volume + new_volume
            pos = acc.position[inst]
            worst = pos + pending if o.side == "bid" else pos - pending
            if abs(worst) > acc.limits.position_limit:
                acc.n_rejects["position_limit"] += 1
                return False
        increase = new_volume > o.volume
        o.volume = new_volume
        if increase:
            self.books[inst].requeue(o)
        return True

    # ---------------- clock ----------------
    def _update_fair_values(self):
        for s in self.stocks.values():
            move = self.rng.gauss(0, s.sigma)
            if s.jump_prob and self.rng.random() < s.jump_prob:
                move += self.rng.gauss(0, s.jump_sigma)
            s.fv = max(1.0, s.fv + move)
            s.history.append(s.fv)

    def _update_pauses(self):
        for inst_id, inst in self.instruments.items():
            should = any(i == inst_id and a <= self.t < b for i, a, b in self.pauses)
            if should and not inst.paused:
                self.books[inst_id].clear()  # resting orders are cancelled at a pause
            inst.paused = should

    def step(self):
        self.step_no += 1
        self.t = round(self.step_no * self.dt, 6)
        self._update_fair_values()
        self._update_pauses()
        order = list(self.actors)
        self.rng.shuffle(order)  # random arrival order = random relative latency each step
        for a in order:
            if self.step_no % a.act_every == a.phase % a.act_every:
                a.act(self)
        for acc in self.accounts.values():
            d = self.net_delta(acc.name)
            if d:
                acc.max_abs_delta = max(acc.max_abs_delta, max(abs(x) for x in d.values()))
        if self.step_no % self.sample_every == 0:
            for acc in self.accounts.values():
                acc.equity_curve.append((self.t, self.pnl(acc.name)))

    # ---------------- scoring ----------------
    def pnl(self, owner, mark="fair"):
        """mark='fair': value positions at true fair value (honest score).
        mark='mid': value each instrument at its own book mid (closer to what a dashboard shows)."""
        acc = self.accounts[owner]
        total = acc.cash
        for inst, pos in acc.position.items():
            if pos == 0:
                continue
            px = self.fv(inst) if mark == "fair" else (self.mid(inst) or self.fv(inst))
            total += pos * px
        return total

    def report(self, owner):
        acc = self.accounts[owner]
        curve = [v for _, v in acc.equity_curve] or [0.0]
        peak, mdd = -math.inf, 0.0
        for v in curve:
            peak = max(peak, v)
            mdd = max(mdd, peak - v)
        return {
            "pnl_fair": round(self.pnl(owner, "fair"), 2),
            "pnl_mid": round(self.pnl(owner, "mid"), 2),
            "max_drawdown": round(mdd, 2),
            "volume": acc.volume_traded,
            "ops": acc.n_ops,
            "rejects": dict(acc.n_rejects),
            "final_positions": {k: v for k, v in acc.position.items() if v},
            "final_net_delta": {k: v for k, v in self.net_delta(owner).items() if v},
            "max_abs_net_delta": acc.max_abs_delta,
        }
