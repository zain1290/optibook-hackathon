"""Derivatives: options, futures and index-tracking ETFs, priced from their underlying stocks.

Standby module: switch it on only if the challenge brief lists such instruments.

Each loop:
  1. fair value of every stock = mid of where real size sits in its book (same as stock_mm)
  2. theoretical value of every derivative:
       option = Black-Scholes(stock fair, strike, time to expiry, vol, rate)
                vol = `vol` if set, else realised vol of the underlying measured live (floor vol_floor)
       future = stock fair * exp(rate * time)
       ETF    = multiplier * sum(shares x stock fair) / divisor + cash component   (ASSUMPTION, see pricing.py)
  3. take: buy any ask at least `deriv_edge` ticks below theo, sell any bid `deriv_edge` ticks above (IOC, deriv_size lots)
  4. hedge: add up the delta of everything we hold per stock (options: Black-Scholes delta; futures ~1;
     ETF: its shares of each constituent) and trade the stock to bring it back inside +/- hedge_band
"""
import math
import time
from collections import defaultdict, deque

from . import pricing
from .common import Ctx, RateBudget
from .stock_mm import kind_of

DERIV_TYPES = ("STOCK_OPTION", "INDEX_OPTION", "STOCK_FUTURE", "INDEX_FUTURE", "INDEX_TRACKING_ETF")


def _fair_from_book(ctx, e, i, depth_lots=200):
    b = e.get_last_price_book(i)
    if not b.bids or not b.asks:
        return None, None, None

    def deep(levels):
        cum = 0
        for pv in levels:
            cum += pv.volume
            if cum >= depth_lots:
                return pv.price
        return levels[-1].price
    return (deep(b.bids) + deep(b.asks)) / 2.0, b.bids, b.asks


class DerivArb:
    name = "deriv_arb"
    LIVE = ("deriv_edge", "deriv_size", "vol", "vol_floor", "hedge_band", "position_limit")

    def __init__(self, pairs=None, position_limit=300, deriv_edge=3, deriv_size=10, vol=None, vol_floor=0.05,
                 hedge_band=10, max_ops_per_sec=20, sim_clock=None, clock=None, hedge_cooldown=0.0, budget=None):
        self.clock = clock or time.monotonic
        self.sim = sim_clock if sim_clock is not None else clock is not None  # sim: compressed option clock
        self.position_limit, self.deriv_edge, self.deriv_size = position_limit, deriv_edge, deriv_size
        self.vol, self.vol_floor, self.hedge_band = vol, vol_floor, hedge_band
        self.budget = budget or RateBudget(max_ops_per_sec, self.clock)
        self.ctx = None
        self.hist = defaultdict(lambda: deque(maxlen=600))  # stock -> (t, fair)
        self.theo, self.deltas = {}, {}
        self.end_time = None

    @property
    def limit(self):
        return self.position_limit

    def realised(self, stock):
        h = list(self.hist[stock])
        if len(h) < 20:
            return None
        dt = max(1e-6, (h[-1][0] - h[0][0]) / (len(h) - 1))
        return pricing.realised_vol([x[1] for x in h], dt, sim=self.sim)

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.position_limit, self.budget)
        ctx, now = self.ctx, self.clock()
        ctx.limit = self.position_limit
        ctx.refresh_instruments()
        inst = ctx.inst
        derivs = [i for i, v in inst.items() if kind_of(v) in DERIV_TYPES and not getattr(v, "paused", False)
                  and not getattr(v, "expired", False)]
        if not derivs:
            return
        stocks = sorted({s for i in derivs for s in self._underlyings(inst[i])})
        fair = {}
        for s in stocks:
            f, _, _ = _fair_from_book(ctx, e, s)
            if f is not None:
                fair[s] = f
                self.hist[s].append((now, f))
        pos = e.get_positions()
        delta = defaultdict(float)
        for i in derivs:
            ins = inst[i]
            th, d = self.value(ins, fair, now)
            if th is None:
                continue
            self.theo[i], self.deltas[i] = th, d
            p = pos.get(i, 0)
            for s, dd in d.items():
                delta[s] += p * dd
            self.take(e, ctx, i, th, pos)
        for s in stocks:  # stock positions count towards delta too
            delta[s] += pos.get(s, 0)
        self.hedge(e, ctx, delta, pos)

    @staticmethod
    def _underlyings(ins):
        if kind_of(ins) == "INDEX_TRACKING_ETF":
            return list((ins.index_constituents or {}).keys())
        return [ins.base_instrument_id] if ins.base_instrument_id else []

    def value(self, ins, fair, now):
        """-> (theoretical value, {stock: delta per lot})"""
        k = kind_of(ins)
        if k == "INDEX_TRACKING_ETF":
            cons = ins.index_constituents or {}
            if any(s not in fair for s in cons):
                return None, {}
            mult, div = ins.etf_multiplier or 1.0, ins.index_divisor or 1.0
            th = pricing.etf_fair_value(fair, cons, div, ins.etf_cash_comp or 0.0, mult)
            return th, {s: mult * w / div for s, w in cons.items()}
        s = ins.base_instrument_id
        if s not in fair:
            return None, {}
        tau = pricing.time_to_expiry(ins.expiry, now, sim=self.sim)
        r = ins.interest_rate or 0.0
        if k in ("STOCK_FUTURE", "INDEX_FUTURE"):
            return pricing.future_fair_value(fair[s], r, tau), {s: math.exp(r * tau)}
        vol = self.vol or max(self.vol_floor, self.realised(s) or 0.0) or None
        if vol is None:
            return None, {}
        th = pricing.bs_price(fair[s], ins.strike, tau, vol, r, ins.option_kind)
        g = pricing.bs_greeks(fair[s], ins.strike, tau, vol, r, ins.option_kind)
        return th, {s: g["delta"]}

    def take(self, e, ctx, i, theo, pos):
        b = e.get_last_price_book(i)
        th = theo / ctx.tick(i)
        if b.asks and th - ctx.t(i, b.asks[0].price) >= self.deriv_edge:
            vol = min(self.deriv_size, b.asks[0].volume, ctx.capacity(i, "bid", pos))
            if vol > 0:
                ctx.ioc(i, "bid", ctx.t(i, b.asks[0].price), vol, tag="deriv_take")
        if b.bids and ctx.t(i, b.bids[0].price) - th >= self.deriv_edge:
            vol = min(self.deriv_size, b.bids[0].volume, ctx.capacity(i, "ask", pos))
            if vol > 0:
                ctx.ioc(i, "ask", ctx.t(i, b.bids[0].price), vol, tag="deriv_take")

    def hedge(self, e, ctx, delta, pos):
        for s, d in delta.items():
            if abs(d) <= self.hedge_band:
                continue
            side = "ask" if d > 0 else "bid"
            vol = min(int(round(abs(d))), ctx.capacity(s, side, pos))
            if vol <= 0:
                continue
            bids, asks = ctx.book(s, exclude_own=True)
            lv = bids if side == "ask" else asks
            if lv:
                ctx.delete_all(s, tag="clear_for_hedge")  # our own quotes would block the hedge (self-trade)
                ctx.ioc(s, side, lv[0][0], vol, tag="delta_hedge")
                ctx.log("delta_hedge", stock=s, delta=round(d, 2), vol=vol)

    def live_params(self):
        return {k: getattr(self, k) for k in self.LIVE}
