"""Evolved strategy: starts as an exact copy of quote_hedge (v0) and is improved round by round.
strategies/quote_hedge.py stays frozen as the original. Each version is a set of feature flags,
so any earlier version can be re-run:  -p version=v0  (see VERSIONS at the bottom).

Original description (v0 = quote_hedge):
v1: quote the illiquid dual listing, hedge every fill on the liquid primary (MADLAD idea, cleaned up).

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
import math

from .common import Ctx, HedgeGuard, RateBudget, hedge_net
from .cross_arb import CrossArb


class Evolved:
    name = "evolved"

    def __init__(self, pairs, position_limit=100, edge=1, size=None, skew_per_lot=0.05,
                 soft_limit=None, take_min_edge=1, penny=True, max_ops_per_sec=20, clock=None, hedge_cooldown=0.0,
                 version="latest", **overrides):
        self.version = LATEST if version == "latest" else version
        self.f = dict(VERSIONS[self.version])
        self.f.update({k: v for k, v in overrides.items() if k in ALL_FLAGS})
        unknown = set(overrides) - ALL_FLAGS
        if unknown:
            raise TypeError(f"unknown params {unknown}")
        self.clock = clock or __import__("time").monotonic
        self.pairs = pairs
        self.limit, self.edge = position_limit, edge
        self.size = size if size is not None else self.f.get("default_size", 10)
        self.skew, self.penny = skew_per_lot, penny
        self.soft = soft_limit if soft_limit is not None else int(position_limit * 0.8)
        self.budget = RateBudget(max_ops_per_sec, clock) if clock else RateBudget(max_ops_per_sec)
        self.taker = CrossArb(pairs, position_limit, min_edge=take_min_edge, hedge=False)
        self.guard = HedgeGuard(hedge_cooldown, clock) if clock else HedgeGuard(hedge_cooldown)
        self.ctx = None
        self._last_tgt = {}
        self._unhedged_since = {}
        self._caps = {}
        self._touch = {}
        self.end_time = None  # set by the runner when the session length is known (or via settings)

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
            self.taker.ctx = self.ctx
        ctx = self.ctx
        ctx.refresh_instruments()
        for P, D in self.pairs:
            if self.f.get("quote_first"):  # fix stale quotes before anything else can use the order budget
                self.quote(ctx, P, D, e.get_positions())
            pos = e.get_positions()
            self.hedge(ctx, P, D, pos)
            pos = e.get_positions()
            self.take(ctx, P, D, pos)
            if not self.f.get("quote_first"):
                self.quote(ctx, P, D, e.get_positions())

    def take(self, ctx, P, D, pos):
        """v0: CrossArb on both legs (IOC). v2 arb_single_leg: take only the scarce dual leg; the hedger
        then lays off the primary leg passively (no IOC cost, no self-trade with our resting hedge)."""
        if not self.f.get("arb_single_leg"):
            self.taker.take(ctx, P, D, pos)
            return
        if ctx.paused(P) or ctx.paused(D):
            return
        pb, pa = ctx.book(P, exclude_own=True)
        db, da = ctx.book(D, exclude_own=True)
        if not (pb and pa and db and da):
            return
        posD, tk = pos.get(D, 0), self.taker
        clip = min(tk.max_clip, self.f.get("max_unhedged", 30))
        unwind_need = tk.unwind_edge
        if self.f.get("arb_cost_aware"):
            # v8: a zero-edge unwind only pays if the hedge leg is ~free (rest inside a >=2 tick primary
            # spread). With a 1 tick spread the hedge crosses, so unwinds need a full tick too.
            if not (pa[0][0] - pb[0][0] >= 2 and self.f.get("passive_hedge")):
                unwind_need = max(unwind_need, tk.min_edge)
        need = unwind_need if posD > 0 else tk.min_edge
        if db[0][0] - pa[0][0] >= need:
            vol = min(db[0][1], clip, ctx.capacity(D, "ask", pos))
            if self.f.get("arb_cost_aware") and need < tk.min_edge:
                vol = min(vol, posD)  # v8: an unwind never overshoots into a new zero-edge position
            if vol > 0:
                ctx.log("arb", pair=[P, D], dir="sell_dual", edge_ticks=db[0][0] - pa[0][0], vol=vol, posD=posD)
                ctx.ioc(D, "ask", db[0][0], vol, tag="arb_dual")
            return
        need = unwind_need if posD < 0 else tk.min_edge
        if pb[0][0] - da[0][0] >= need:
            vol = min(da[0][1], clip, ctx.capacity(D, "bid", pos))
            if self.f.get("arb_cost_aware") and need < tk.min_edge:
                vol = min(vol, -posD)
            if vol > 0:
                ctx.log("arb", pair=[P, D], dir="buy_dual", edge_ticks=pb[0][0] - da[0][0], vol=vol, posD=posD)
                ctx.ioc(D, "bid", da[0][0], vol, tag="arb_dual")

    # ------------------------------------------------------------------ hedging
    def hedge(self, ctx, P, D, pos):
        """v0: IOC across the primary spread (pays ~half the spread).
        v1 passive_hedge: if the primary spread is >= 2 ticks, rest the hedge INSIDE it (at mid), where the
        primary's heavy customer flow fills it at ~zero cost. Fall back to IOC after hedge_timeout seconds,
        if the unhedged size exceeds max_unhedged, if the spread is 1 tick, or if the primary is paused."""
        f = self.f
        if not f.get("passive_hedge"):
            hedge_net(ctx, P, D, pos, guard=self.guard)
            return
        net = pos.get(P, 0) + pos.get(D, 0)
        now = self.clock()
        if f.get("adaptive_touch"):
            self._learn_touch(P, net, now)
        mine = list(ctx.e.get_outstanding_orders(P).values())
        if net == 0:
            self._unhedged_since.pop(P, None)
            for o in mine:
                ctx.delete(P, o.order_id, tag="hedge_cancel")
            return
        since = self._unhedged_since.setdefault(P, now)
        side = "ask" if net > 0 else "bid"
        pb, pa = ctx.book(P, exclude_own=True)
        spread = pa[0][0] - pb[0][0] if pb and pa else 0
        urgent = (now - since > f.get("hedge_timeout", 1.0) or abs(net) > f.get("max_unhedged", 30)
                  or spread < 2 or ctx.paused(P))
        if urgent:
            for o in mine:
                ctx.delete(P, o.order_id, tag="hedge_cancel")
            hedge_net(ctx, P, D, ctx.e.get_positions(), guard=self.guard)
            return
        px = (pb[0][0] + pa[0][0] + (1 if side == "ask" else 0)) // 2  # strictly inside the spread
        use_touch = bool(f.get("touch_secs")) and now - since < f["touch_secs"]
        if use_touch and f.get("adaptive_touch"):
            use_touch = self._touch_ok(P, net, now)
        if use_touch:
            # v5 ladder: first offer the hedge AT the touch (earn the half spread if flow comes),
            # then step inside to mid, then IOC after hedge_timeout
            px = pa[0][0] if side == "ask" else pb[0][0]
        same = [o for o in mine if o.side == side and ctx.t(P, o.price) == px]
        for o in mine:
            if o not in same:
                ctx.delete(P, o.order_id, tag="hedge_cancel")
        have, need = sum(o.volume for o in same), abs(net)
        for o in reversed(same):  # too much resting: shrink the newest first (keeps the oldest queue spot)
            if have <= need:
                break
            cut = min(o.volume, have - need)
            if cut == o.volume:
                ctx.delete(P, o.order_id, tag="hedge_cancel")
            else:
                ctx.amend(P, o.order_id, o.volume - cut, tag="hedge_shrink")
            have -= cut
        if have < need:
            v = min(need - have, ctx.capacity(P, side, ctx.e.get_positions()))
            if v > 0:
                ctx.limit_order(P, side, px, v, tag="hedge_passive")

    def _learn_touch(self, P, net, now):
        """v6: did the hedge resting AT the touch get filled? Measured from our own position changes:
        |net| fell while the touch order was the only hedge working -> success. Ran out of touch time -> miss."""
        st = self._touch.setdefault(P, {"ema": 1.0, "prev": None, "active": False, "probe_t": -1e18})
        prev = st["prev"]
        if st["active"] and prev is not None:
            if net == 0 or (net * prev > 0 and abs(net) < abs(prev)):
                st["ema"] = 0.9 * st["ema"] + 0.1 * 1.0
                st["active"] = net != 0
            elif net * prev > 0 and now - self._unhedged_since.get(P, now) >= self.f["touch_secs"]:
                st["ema"] = 0.9 * st["ema"] + 0.1 * 0.0
                st["active"] = False
        st["prev"] = net

    def _touch_ok(self, P, net, now):
        st = self._touch.setdefault(P, {"ema": 1.0, "prev": None, "active": False, "probe_t": -1e18})
        ok = st["ema"] >= self.f.get("touch_min_rate", 0.35)
        if not ok and now - st["probe_t"] > self.f.get("touch_probe_secs", 30.0):
            st["probe_t"], ok = now, True  # occasional re-test: market behaviour can change
        st["active"] = ok
        return ok

    # ------------------------------------------------------------------ quoting
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
        if self.f.get("skew_start") is not None:
            # v4: the dual position is hedged on the primary, so it carries no price risk; only lean on it
            # when it gets near the position limit (keeps both sides quoting at the best price otherwise)
            over = max(0, abs(posD) - self.f["skew_start"])
            shift = int(round(over * self.skew * 2)) * (1 if posD > 0 else -1)
        if self.f.get("cost_quote"):
            # v3: price from fair value and what hedging will actually cost in THIS market:
            #   bid = fair - (hedge cost + min profit), ask = fair + (...), on the tick grid.
            # hedge cost: resting inside a >=2 tick primary spread ~passive_cost; else crossing = half spread.
            pb, pa = ctx.book(P, exclude_own=True)  # v3 fix: our own resting hedge is not the market
            if not (pb and pa):
                return None
            spread = pa[0][0] - pb[0][0]
            cost = self.f["passive_cost"] if (spread >= 2 and self.f.get("passive_hedge")) else spread / 2
            fair = (pb[0][0] + pa[0][0]) / 2
            need = cost + self.f["min_profit"]
            bid = math.floor(fair - need + 1e-9) - shift
            ask = math.ceil(fair + need - 1e-9) - shift
            bid = min(bid, math.floor(fair - (need if posD >= 0 else cost) + 1e-9))
            ask = max(ask, math.ceil(fair + (need if posD <= 0 else cost) - 1e-9))
        else:
            bid = pb[0][0] - self.edge - shift
            ask = pa[0][0] + self.edge - shift
            # opening trades need the full edge; unwinding trades may accept less, but never a loss
            # vs the hedge price (buy dual <= primary bid, sell dual >= primary ask)
            bid = min(bid, pb[0][0] - (self.edge if posD >= 0 else 0))
            ask = max(ask, pa[0][0] + (self.edge if posD <= 0 else 0))
        if self.f.get("queue_jump") and self.f.get("cost_quote"):
            # v9: rivals queued at our price split the flow. If our hedges are EARNING (touch hedges fill,
            # measured live), stepping 1 tick ahead of the queue still pays: ~0 on the quote + hedge edge.
            tst = self._touch.get(P, {})
            hedges_earn = (spread >= 2 and tst.get("ema", 0) >= self.f.get("touch_min_rate", 0.35))
            qmin = self.f.get("queue_min", 5)
            if hedges_earn:
                lim_b = math.floor(fair - self.f.get("jump_margin", 0.0) + 1e-9)
                lim_a = math.ceil(fair + self.f.get("jump_margin", 0.0) - 1e-9)
                if db and db[0][0] == bid and db[0][1] >= qmin and bid + 1 <= lim_b and posD < self.soft // 2:
                    bid += 1
                if da and da[0][0] == ask and da[0][1] >= qmin and ask - 1 >= lim_a and posD > -self.soft // 2:
                    ask -= 1
        self._caps[D] = (bid, ask)  # worst prices we accept; pennying only moves quotes away from these
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
        wd = self.f.get("wind_down_secs")
        if wd and self.end_time is not None and self.clock() >= self.end_time - wd:
            # v7: final stretch: only quote the side that shrinks the dual inventory, at the unwind price,
            # so the session ends (nearly) flat without dumping into the thin book
            bv = min(self.size, -posD) if posD < 0 else 0
            av = min(self.size, posD) if posD > 0 else 0
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
            stick = self.f.get("sticky_ticks", 0)
            cap = self._caps.get(D, (None, None))[0 if side == "bid" else 1]
            for o in mine:
                p0 = ctx.t(D, o.price)
                ok = p0 == price
                if stick and cap is not None and vol > 0:  # v2: keep a quote that is still safe and close enough
                    ok = (price - stick <= p0 <= cap) if side == "bid" else (cap <= p0 <= price + stick)
                if keep is None and ok and vol > 0:
                    keep = o
                else:
                    ctx.delete(D, o.order_id, tag="requote")
            if vol <= 0:
                continue
            if keep is not None:
                if keep.volume > vol:
                    ctx.amend(D, keep.order_id, vol, tag="shrink")  # shrinking keeps queue priority
                continue  # same price: leave it alone (keeps queue priority, saves rate limit)
            if self.budget.left() <= self.f.get("budget_reserve", 0):
                continue  # v2: leave room in the order budget for hedges and cancels
            # worst-case capacity: other-side orders don't count; same-side ones were just deleted
            v = min(vol, ctx.capacity(D, side, pos, {}))
            if v > 0:
                ctx.limit_order(D, side, price, v, tag="quote")


# ---------------------------------------------------------------------------------------------
# Versions: each round's improvement is a flag. A version = the flags switched on at that point.
FLAGS_BY_VERSION = [
    ("v0", {}),  # identical to quote_hedge
    # round 1 logs: hedges paid -1.00 tick/lot (13.3 of the 19.1 quote edge); primary spread is 2 ticks
    ("v1", {"passive_hedge": True, "hedge_timeout": 1.0, "max_unhedged": 30}),
    # round 2 logs: quote fills at -0.59 ticks (stale, picked off), 1851 requotes, 106 throttled orders,
    # one arb leg rejected as self-trade against our resting hedge -> 33 lots hedged by IOC
    ("v2", {"sticky_ticks": 1, "quote_first": True, "arb_single_leg": True}),  # budget_reserve tested: no effect
    # round 3 + bench: hedging now costs ~0.4 tick, rivals pay ~1; quoting tighter (edge 0) won 6/8 markets.
    # Generalised: quote at fair +- (expected hedge cost + min profit), and stop reading our own hedge as market
    ("v3", {"cost_quote": True, "passive_cost": 0.4, "min_profit": 0.5}),
    # round 4 logs: inventory skew pushed quotes 1-2 ticks off the touch 70% of the time while net delta
    # was non-zero only 7.7% of the time -> skew only as a position-limit guard
    ("v4", {"skew_start": 50}),
    # round 5 logs: passive hedges cost -0.27 tick/lot (-17.5 vs +32.1 earned by quotes)
    ("v5", {"touch_secs": 0.4}),  # bench only: +33 PnL, but ~0 when the primary MM keeps queue priority (artifact)
    # adaptive version: measure our own touch-hedge fill rate, skip the touch step where it doesn't fill
    ("v6", {"adaptive_touch": True, "touch_min_rate": 0.35, "touch_probe_secs": 30.0}),
    # round 6 logs: closing +62 dual / -62 primary at the end cost -18.8 (dual book is thin).
    # Tried wind_down_secs=60 (one-sided quoting in the final minute): WORSE (-1 to -4 PnL), rejected.
    # Adopted instead (runner, not strategy): exit mode 'net' = close only unhedged delta (+5.5 PnL).
    ("v7", {}),
    # tight-market experiments: arb unwound inventory at 0 edge (2,200 lots) while every hedge paid half a
    # tick; unwinds could also overshoot through zero into new zero-edge positions
    ("v8", {"arb_cost_aware": True}),
    # clone test (half the field runs v8): we fall to rank ~3, flow split in a queue at the same price.
    # Tried queue_jump (step 1 tick ahead of a queue, betting on hedge edge): WORSE everywhere, rejected.
    # Adopted: faster loop (execution, not logic): 0.1 s loop rank 2.4 vs 0.2 s 3.3 vs 0.5 s 4.1 vs clones.
    ("v9", {}),
    # round 9 logs: top clone traded 1518 lots vs our 1162. Size 15 wins on BOTH crowded and clone markets
    # (hedge_timeout=2.0 tested: mixed, not adopted)
    ("v10", {"default_size": 15}),
]
VERSIONS = {}
_acc = {}
for _name, _flags in FLAGS_BY_VERSION:
    _acc = {**_acc, **_flags}
    VERSIONS[_name] = dict(_acc)
LATEST = FLAGS_BY_VERSION[-1][0]
ALL_FLAGS = set(k for _, fl in FLAGS_BY_VERSION for k in fl)
