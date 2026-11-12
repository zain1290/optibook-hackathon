"""Helpers shared by strategies. Uses ONLY the optibook Exchange API, so it runs live unchanged."""
import time
from collections import deque


class RateBudget:
    """Client-side rate limiter. Stay under the exchange limit so orders are never rejected.
    clock: callable returning seconds (sim time in the simulator, time.monotonic live)."""

    def __init__(self, max_ops_per_sec=20, clock=time.monotonic, reserve=0):
        self.max, self.clock, self.ops = max_ops_per_sec, clock, deque()
        self.reserve = reserve  # ops per second kept free for URGENT actions (pick-offs, safety cancels)

    def _trim(self):
        now = self.clock()
        while self.ops and self.ops[0] <= now - 1.0 + 1e-9:
            self.ops.popleft()

    def left(self):
        self._trim()
        return self.max - len(self.ops)

    def take(self, n=1, urgent=True):
        self._trim()
        if len(self.ops) + n > self.max - (0 if urgent else self.reserve):
            return False
        now = self.clock()
        self.ops.extend([now] * n)
        return True


class Ctx:
    """Thin wrapper around the exchange: tick maths, books, capacity, safe order calls."""

    def __init__(self, e, position_limit=100, budget: RateBudget = None):
        self.e = e
        self.limit = position_limit
        self.budget = budget or RateBudget()
        self.inst = e.get_instruments()
        # optional hooks provided by runlog.LoggingExchange (no-ops on the raw exchange)
        self._log = getattr(e, "log_event", None)
        self._tag = getattr(e, "tag_next", None)

    def log(self, kind, **data):
        if self._log:
            self._log(kind, **data)

    # actions that protect us or make money right now may use the reserved part of the order budget
    URGENT = {None, "take", "cancel_stale", "news_pull", "news", "clear_for_hedge", "delta_hedge", "flatten",
              "hedge", "hedge_on_dual", "arb", "deriv_take", "pairs"}

    def _take(self, tag=None):
        if self.budget.take(1, urgent=tag in self.URGENT):
            return True
        self.log("throttled")  # counted, not written line by line
        return False

    def refresh_instruments(self):
        self.inst = self.e.get_instruments()

    def tick(self, i):
        return self.inst[i].tick_size

    def paused(self, i):
        return bool(getattr(self.inst[i], "paused", False))

    def px(self, i, ticks):
        return round(ticks * self.tick(i), 6)

    def t(self, i, price):
        return int(round(price / self.tick(i)))

    def book(self, i, exclude_own=False):
        """Returns (bids, asks) as lists of (price_ticks, volume), best first.
        exclude_own=True removes our resting orders, so we can see where OTHERS are."""
        b = self.e.get_last_price_book(i)
        bids = [(self.t(i, pv.price), pv.volume) for pv in b.bids]
        asks = [(self.t(i, pv.price), pv.volume) for pv in b.asks]
        if exclude_own:
            own = self.e.get_outstanding_orders(i).values()
            sub = {}
            for o in own:
                sub[(o.side, self.t(i, o.price))] = sub.get((o.side, self.t(i, o.price)), 0) + o.volume
            bids = [(p, v - sub.get(("bid", p), 0)) for p, v in bids]
            asks = [(p, v - sub.get(("ask", p), 0)) for p, v in asks]
            bids = [(p, v) for p, v in bids if v > 0]
            asks = [(p, v) for p, v in asks if v > 0]
        return bids, asks

    def capacity(self, i, side, positions, outstanding=None):
        """How much more we can BUY (side='bid') or SELL (side='ask') without breaching the limit
        in the worst case where all our resting orders on that side also fill."""
        pos = positions.get(i, 0)
        outstanding = self.e.get_outstanding_orders(i) if outstanding is None else outstanding
        pending = sum(o.volume for o in outstanding.values() if o.side == side)
        if side == "bid":
            return max(0, self.limit - pos - pending)
        return max(0, self.limit + pos - pending)

    def ioc(self, i, side, price_ticks, volume, tag=None):
        if volume <= 0 or not self._take(tag):
            return None
        if self._tag:
            self._tag(tag)
        return self.e.insert_order(i, price=self.px(i, price_ticks), volume=int(volume), side=side,
                                   order_type="ioc")

    def limit_order(self, i, side, price_ticks, volume, tag=None):
        if volume <= 0 or not self._take(tag):
            return None
        if self._tag:
            self._tag(tag)
        return self.e.insert_order(i, price=self.px(i, price_ticks), volume=int(volume), side=side,
                                   order_type="limit")

    def delete(self, i, order_id, tag=None):
        if not self._take(tag):
            return False
        if self._tag:
            self._tag(tag)
        return self.e.delete_order(i, order_id=order_id)

    def delete_all(self, i, tag=None):
        if not self._take(tag):
            return False
        if self._tag:
            self._tag(tag)
        return self.e.delete_orders(i)

    def amend(self, i, order_id, volume, tag=None):
        if not self._take(tag):
            return False
        if self._tag:
            self._tag(tag)
        return self.e.amend_order(i, order_id=order_id, volume=int(volume))


class HedgeGuard:
    """Live-trading guard against double hedging: after sending a hedge, wait `cooldown` seconds
    for positions to update before hedging the same pair again (0 in the sim, ~0.2s live)."""

    def __init__(self, cooldown=0.0, clock=time.monotonic):
        self.cooldown, self.clock, self.last = cooldown, clock, {}

    def ready(self, key):
        return self.clock() - self.last.get(key, -1e9) >= self.cooldown

    def mark(self, key):
        self.last[key] = self.clock()


def hedge_net(ctx: Ctx, primary, dual, positions, max_slip_ticks=2, max_unhedged_if_paused=20,
              guard: HedgeGuard = None):
    """Flatten net delta (pos_primary + pos_dual) by trading the liquid primary listing with IOC.
    Stateless: works from positions only, so partial fills and missed legs are fixed next loop."""
    net = positions.get(primary, 0) + positions.get(dual, 0)
    if net == 0 or (guard and not guard.ready(primary)):
        return 0
    if guard:
        guard.mark(primary)
    venue = primary
    if ctx.paused(primary):
        if abs(net) <= max_unhedged_if_paused or ctx.paused(dual):
            return 0
        venue = dual  # emergency: hedge on the illiquid book if primary is closed
    bids, asks = ctx.book(venue)
    side = "ask" if net > 0 else "bid"
    lvls = bids if side == "ask" else asks
    if not lvls:
        return 0
    cap = ctx.capacity(venue, side, positions)
    vol = min(abs(net), cap)
    worst = lvls[0][0] - max_slip_ticks if side == "ask" else lvls[0][0] + max_slip_ticks
    ctx.ioc(venue, side, worst, vol, tag="hedge" if venue == primary else "hedge_on_dual")
    ctx.log("hedge", pair=[primary, dual], net=net, venue=venue, vol=vol, limit_px=ctx.px(venue, worst))
    return vol


def flatten_net(e, pairs, slip_ticks=5, others=()):
    """Exit mode 'net': cancel everything and close only the UNHEDGED part (primary + dual net delta),
    trading the liquid primary. A hedged pair (long dual / short primary) has no price risk.
    `others`: instruments outside any pair (single stocks): those are closed completely."""
    if others:
        flatten_all(e, list(others), slip_ticks)
    ctx = Ctx(e)
    ctx.log("flatten_net", positions=e.get_positions())
    for P, D in pairs:
        e.delete_orders(P)
        e.delete_orders(D)
    pos = e.get_positions()
    for P, D in pairs:
        net = pos.get(P, 0) + pos.get(D, 0)
        venue = P if not ctx.paused(P) else D
        if net == 0 or ctx.paused(venue):
            continue
        bids, asks = ctx.book(venue)
        if ctx._tag:
            ctx._tag("flatten")
        if net > 0 and bids:
            e.insert_order(venue, price=ctx.px(venue, bids[0][0] - slip_ticks), volume=net, side="ask", order_type="ioc")
        elif net < 0 and asks:
            e.insert_order(venue, price=ctx.px(venue, asks[0][0] + slip_ticks), volume=-net, side="bid", order_type="ioc")


FLATTEN_PACE = 0.0  # seconds between closing requests; run_live sets 0.08 live (the exchange cuts the
                    # connection above ~25 requests/s, and a cut would leave positions open)


def _pace():
    if FLATTEN_PACE:
        time.sleep(FLATTEN_PACE)


def flatten_all(e, instruments, slip_ticks=5):
    """End of session / emergency: cancel everything and close all positions with IOC."""
    ctx = Ctx(e)
    ctx.log("flatten_all", positions=e.get_positions())
    for i in instruments:
        e.delete_orders(i)
        _pace()
    pos = e.get_positions()
    for i in instruments:
        p = pos.get(i, 0)
        if p == 0 or ctx.paused(i):
            continue
        bids, asks = ctx.book(i)
        if ctx._tag:
            ctx._tag("flatten")
        if p > 0 and bids:
            e.insert_order(i, price=ctx.px(i, bids[0][0] - slip_ticks), volume=p, side="ask", order_type="ioc")
            _pace()
        elif p < 0 and asks:
            e.insert_order(i, price=ctx.px(i, asks[0][0] + slip_ticks), volume=-p, side="bid", order_type="ioc")
            _pace()
