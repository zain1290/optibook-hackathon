"""v1: quote the illiquid dual listing, hedge every fill on the liquid primary (MADLAD idea, cleaned up).

Each loop, per (primary, dual) pair:
  1. hedge: flatten net delta on the primary (IOC)
  2. take:  run CrossArb on anyone else's crossed quotes
  3. quote: bid on dual at (primary best bid - edge), ask at (primary best ask + edge)
            -> every fill can be hedged immediately on the primary for ~edge ticks profit
     tricks:
       - don't overpay: only improve the best OTHER quote by 1 tick, never beyond the target
       - inventory skew: shift both quotes against our dual inventory so it recycles
       - only touch an order when its price must change (saves rate limit, keeps queue priority)
       - pull quotes when the primary is paused (fills could not be hedged)
"""
from .common import Ctx, HedgeGuard, RateBudget, hedge_net
from .cross_arb import CrossArb


class QuoteHedge:
    name = "quote_hedge"

    def __init__(self, pairs, position_limit=100, edge=1, size=10, skew_per_lot=0.05,
                 soft_limit=None, take_min_edge=1, penny=True, max_ops_per_sec=20, clock=None, hedge_cooldown=0.0):
        self.pairs = pairs
        self.limit, self.edge, self.size = position_limit, edge, size
        self.skew, self.penny = skew_per_lot, penny
        self.soft = soft_limit if soft_limit is not None else int(position_limit * 0.8)
        self.budget = RateBudget(max_ops_per_sec, clock) if clock else RateBudget(max_ops_per_sec)
        self.taker = CrossArb(pairs, position_limit, min_edge=take_min_edge, hedge=False)
        self.guard = HedgeGuard(hedge_cooldown, clock) if clock else HedgeGuard(hedge_cooldown)
        self.ctx = None
        self._last_tgt = {}

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
            self.taker.ctx = self.ctx
        ctx = self.ctx
        ctx.refresh_instruments()
        for P, D in self.pairs:
            pos = e.get_positions()
            hedge_net(ctx, P, D, pos, guard=self.guard)
            pos = e.get_positions()
            self.taker.take(ctx, P, D, pos)
            self.quote(ctx, P, D, e.get_positions())

    def targets(self, ctx, P, D, pos):
        """Desired (bid_ticks, bid_vol, ask_ticks, ask_vol) on the dual, or None to pull quotes."""
        if ctx.paused(P) or ctx.paused(D):
            self._pulled(ctx, D, "paused")
            return None
        pb, pa = ctx.book(P)
        if not (pb and pa):
            self._pulled(ctx, D, "primary book empty")
            return None
        db, da = ctx.book(D, exclude_own=True)
        posD = pos.get(D, 0)
        shift = int(round(posD * self.skew))  # long dual -> quote lower to sell it, buy less eagerly
        bid = pb[0][0] - self.edge - shift
        ask = pa[0][0] + self.edge - shift
        # opening trades need the full edge; unwinding trades may accept less, but never a loss
        # vs the hedge price (buy dual <= primary bid, sell dual >= primary ask)
        bid = min(bid, pb[0][0] - (self.edge if posD >= 0 else 0))
        ask = max(ask, pa[0][0] + (self.edge if posD <= 0 else 0))
        if self.penny:
            if db and db[0][0] + 1 < bid:
                bid = db[0][0] + 1
            if da and da[0][0] - 1 > ask:
                ask = da[0][0] - 1
        if da and bid >= da[0][0]:
            bid = da[0][0] - 1  # don't cross (the taker handles real crosses)
        if db and ask <= db[0][0]:
            ask = db[0][0] + 1
        bv = self.size if posD < self.soft else 0
        av = self.size if posD > -self.soft else 0
        tgt = (bid, bv, ask, av)
        if self._last_tgt.get(D) != tgt:  # log the inputs behind every quote change
            self._last_tgt[D] = tgt
            ctx.log("quote_target", inst=D, bid=ctx.px(D, bid), bid_vol=bv, ask=ctx.px(D, ask), ask_vol=av,
                    primary_bbo=[ctx.px(P, pb[0][0]), ctx.px(P, pa[0][0])],
                    others_bbo=[ctx.px(D, db[0][0]) if db else None, ctx.px(D, da[0][0]) if da else None],
                    posD=posD, shift=shift, edge=self.edge, size=self.size, penny=self.penny)
        return tgt

    def _pulled(self, ctx, D, why):
        if self._last_tgt.get(D) != why:
            self._last_tgt[D] = why
            ctx.log("quotes_pulled", inst=D, reason=why)

    def quote(self, ctx, P, D, pos):
        tgt = self.targets(ctx, P, D, pos)
        outstanding = ctx.e.get_outstanding_orders(D)
        if tgt is None:
            if outstanding:
                ctx.delete_all(D, tag="pull")
            return
        bid, bv, ask, av = tgt
        for side, price, vol in (("bid", bid, bv), ("ask", ask, av)):
            mine = [o for o in outstanding.values() if o.side == side]
            keep = None
            for o in mine:
                if keep is None and ctx.t(D, o.price) == price and vol > 0:
                    keep = o
                else:
                    ctx.delete(D, o.order_id, tag="requote")
            if vol <= 0:
                continue
            if keep is not None:
                if keep.volume > vol:
                    ctx.amend(D, keep.order_id, vol, tag="shrink")  # shrinking keeps queue priority
                continue  # same price: leave it alone (keeps queue priority, saves rate limit)
            # worst-case capacity: other-side orders don't count; same-side ones were just deleted
            v = min(vol, ctx.capacity(D, side, pos, {}))
            if v > 0:
                ctx.limit_order(D, side, price, v, tag="quote")
