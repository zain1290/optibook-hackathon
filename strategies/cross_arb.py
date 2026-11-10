"""v0: take-only dual-listing arbitrage. The simplest thing that can make money.

When the dual's bid is above the primary's ask (or vice versa) by >= min_edge ticks:
  1. hit the SCARCE leg first (illiquid dual), because it is the one that disappears,
  2. trade the liquid primary leg for the same size,
  3. every loop, flatten any leftover net delta on the primary (fixes partial fills).
Trades that REDUCE our dual inventory only need `unwind_edge` (default 0), so inventory
gets recycled instead of hitting the position limit and freezing one direction.
"""
from .common import Ctx, HedgeGuard, RateBudget, hedge_net


class CrossArb:
    name = "cross_arb"

    def __init__(self, pairs, position_limit=100, min_edge=1, unwind_edge=0, max_clip=50,
                 max_ops_per_sec=20, clock=None, hedge=True, hedge_cooldown=0.0):
        self.pairs = pairs  # [(primary, dual), ...]
        self.limit, self.min_edge, self.unwind_edge = position_limit, min_edge, unwind_edge
        self.max_clip, self.hedge = max_clip, hedge
        self.budget = RateBudget(max_ops_per_sec, clock) if clock else RateBudget(max_ops_per_sec)
        self.guard = HedgeGuard(hedge_cooldown, clock) if clock else HedgeGuard(hedge_cooldown)
        self.ctx = None

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
        ctx = self.ctx
        ctx.refresh_instruments()
        for P, D in self.pairs:
            pos = e.get_positions()
            if self.hedge:
                hedge_net(ctx, P, D, pos, guard=self.guard)
                pos = e.get_positions()
            self.take(ctx, P, D, pos)

    def take(self, ctx, P, D, pos):
        if ctx.paused(P) or ctx.paused(D):
            return
        pb, pa = ctx.book(P, exclude_own=True)
        db, da = ctx.book(D, exclude_own=True)
        if not (pb and pa and db and da):
            return
        posD = pos.get(D, 0)
        # Direction 1: sell dual at its bid, buy primary at its ask
        need = self.unwind_edge if posD > 0 else self.min_edge
        if db[0][0] - pa[0][0] >= need:
            vol = min(db[0][1], pa[0][1], self.max_clip,
                      ctx.capacity(D, "ask", pos), ctx.capacity(P, "bid", pos))
            if vol > 0:
                ctx.ioc(D, "ask", db[0][0], vol)
                ctx.ioc(P, "bid", pa[0][0], vol)
                return
        # Direction 2: buy dual at its ask, sell primary at its bid
        need = self.unwind_edge if posD < 0 else self.min_edge
        if pb[0][0] - da[0][0] >= need:
            vol = min(da[0][1], pb[0][1], self.max_clip,
                      ctx.capacity(D, "bid", pos), ctx.capacity(P, "ask", pos))
            if vol > 0:
                ctx.ioc(D, "bid", da[0][0], vol)
                ctx.ioc(P, "ask", pb[0][0], vol)
