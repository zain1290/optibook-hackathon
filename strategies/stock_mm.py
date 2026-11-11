"""Stock market maker for the Bona Fide setup: many independent stocks, one big exchange maker per book.

The exchange maker quotes a few ticks wide with thousands of lots. Background traders hit the best
price with 20 lots. If our quote is 1 tick better than the maker's, those trades hit US first, and we
earn the gap between our price and fair value on every lot.

Each loop, per stock:
  1. fair value = mid of the prices where real size sits (depth_lots), ignoring our own orders: the
     exchange maker's big quotes are centred on fair value, small rival orders inside the spread are not
  2. target bid = min(best other bid + inside, fair - quote_edge - skew), ask mirrored
     skew = skew_per_lot * position: a long position lowers both quotes so we sell more than we buy
  3. only touch an order when its price must change (saves rate limit, keeps our place in the queue);
     orders that became too aggressive (fair moved through them) are cancelled first, across all stocks
  4. news: a post naming a stock (or its sector) pulls our quotes on it for news_pause seconds; with
     news_trade_size > 0 we also trade in the direction of the news before the maker reprices
  5. near the end (end_time), inventory limits shrink to zero so we finish flat
  6. take: buy/sell straight away when someone else's quote is take_edge ticks through fair value
     (stale or inventory-dumping rival quotes), never building a position past the soft limit.
     This was the biggest win in the simulator; set take_edge=0 to switch it off.
"""
import math
import time

from .common import Ctx, RateBudget
from .news import read_post

STOCK_TYPES = ("STOCK", None, "")


class _Own:
    """Our resting order, in ticks (the real client's objects may not allow extra attributes)."""
    __slots__ = ("order_id", "side", "price_t", "volume", "gone")

    def __init__(self, order_id, side, price_t, volume):
        self.order_id, self.side, self.price_t, self.volume, self.gone = order_id, side, price_t, volume, False


def kind_of(ins):
    """Normalised instrument type name ('STOCK', 'STOCK_OPTION', ...) for sim strings and real enums."""
    t = getattr(ins, "instrument_type", None)
    if t is None:
        return None
    return getattr(t, "name", None) or str(t).split(".")[-1].upper()


class StockMM:
    name = "stock_mm"
    LIVE = ("size", "inside", "quote_edge", "skew_per_lot", "soft_limit", "position_limit", "sticky_ticks",
            "take_edge", "take_size", "news_pause", "news_trade_size", "news_min_score", "wind_down_s",
            "max_stocks", "fair", "depth_lots", "quote_mode")

    def __init__(self, pairs=None, instruments=None, position_limit=300, soft_limit=None, size=10, inside=1,
                 quote_edge=1.5, skew_per_lot=0.02, sticky_ticks=2, take_edge=1, take_size=20, news_pause=3.0,
                 news_trade_size=0, news_min_score=1, wind_down_s=60.0, max_stocks=0, fair="deep", depth_lots=200,
                 quote_mode="both", reserve_ops=6, max_ops_per_sec=20, clock=None, hedge_cooldown=0.0):
        self.clock = clock or time.monotonic
        self.instruments = [s for s in instruments.split(",")] if isinstance(instruments, str) else instruments
        self.position_limit, self.size, self.inside, self.quote_edge = position_limit, size, inside, quote_edge
        self.soft_limit = soft_limit if soft_limit is not None else position_limit // 3  # 100 of 300: same PnL, less risk
        self.skew_per_lot, self.sticky_ticks = skew_per_lot, sticky_ticks
        self.take_edge, self.take_size = take_edge, take_size
        self.news_pause, self.news_trade_size, self.news_min_score = news_pause, news_trade_size, news_min_score
        self.wind_down_s, self.max_stocks, self.fair, self.depth_lots = wind_down_s, max_stocks, fair, depth_lots
        self.budget = RateBudget(max_ops_per_sec, self.clock, reserve=reserve_ops)
        self.ctx = None
        self.ids = []
        self.pause_until = {}
        self.end_time = None
        self._t_refresh = -1e18
        self._rr = 0
        self.last_fair = {}
        self.quote_mode = quote_mode  # both | reduce (only the side that shrinks our position) | off
        self.extra_delta = {}  # stock -> delta held through derivatives (set by combo); worked off via skew

    # ------------------------------------------------------------------ setup
    @property
    def limit(self):  # runner / pause helper read .limit
        return self.position_limit

    def _refresh(self, e):
        now = self.clock()
        if now - self._t_refresh < 5.0 and self.ids:
            return
        self._t_refresh = now
        get = getattr(e, "get_tradable_instruments", None) or e.get_instruments
        try:
            inst = get()
        except Exception:
            inst = e.get_instruments()
        self.ctx.inst.update(inst)
        ids = [i for i, v in inst.items() if kind_of(v) in STOCK_TYPES and not getattr(v, "paused", False)
               and not getattr(v, "expired", False)]
        if self.instruments:
            ids = [i for i in ids if i in self.instruments]
        self.ids = sorted(ids)

    # ------------------------------------------------------------------ main loop
    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.position_limit, self.budget)
        ctx = self.ctx
        ctx.limit = self.position_limit
        self._refresh(e)
        now = self.clock()
        self.on_news(e, ctx, now)
        pos = e.get_positions()
        plans, dangerous = [], []
        for i in self.ids:
            plan = self.plan(e, ctx, i, pos, now)
            if plan is None:
                continue
            plans.append(plan)
            for side, (px, vol) in plan["want"].items():
                for o in plan["own"][side]:
                    if (px is None or (side == "bid" and o.price_t > px) or (side == "ask" and o.price_t < px)):
                        dangerous.append((i, o))
        for i, o in dangerous:  # first: pull anything the market moved through, on every stock
            ctx.delete(i, o.order_id, tag="cancel_stale")
            o.gone = True
        if self.take_edge:  # second: pick off stale / dumped quotes (after our own stale ones are gone)
            for plan in plans:
                if "fair" in plan:
                    self.take(e, ctx, plan["i"], plan["fair"], plan["bids"], plan["asks"], pos, plan["own"])
        if self.max_stocks:
            plans.sort(key=lambda p: -p["spread"])
            plans = plans[: int(self.max_stocks)]
        n = len(plans)
        for k in range(n):  # then: place / move quotes, rotating which stock goes first
            self.reconcile(ctx, plans[(self._rr + k) % n])
        self._rr += 1

    # ------------------------------------------------------------------ news
    def on_news(self, e, ctx, now):
        poll = getattr(e, "poll_new_social_media_feeds", None)
        if poll is None:
            return
        try:
            posts = poll() or []
        except Exception:
            return
        for p in posts:
            insts, score, text, ts = read_post(p, self.ids)
            ctx.log("news", text=text[:200], instruments=insts, score=score, ts=ts)
            for i in insts:
                self.pause_until[i] = now + self.news_pause
                ctx.delete_all(i, tag="news_pull")
                if self.news_trade_size and abs(score) >= self.news_min_score:
                    self.news_trade(e, ctx, i, 1 if score > 0 else -1)

    def news_trade(self, e, ctx, i, sign):
        bids, asks = ctx.book(i, exclude_own=True)
        pos = e.get_positions()
        side = "bid" if sign > 0 else "ask"
        lv = asks if sign > 0 else bids
        if not lv:
            return
        vol = min(int(self.news_trade_size), ctx.capacity(i, side, pos))
        if vol > 0:
            ctx.ioc(i, side, lv[0][0], vol, tag="news")

    # ------------------------------------------------------------------ quoting
    def plan(self, e, ctx, i, pos, now):
        own_raw = e.get_outstanding_orders(i)
        own = {"bid": [], "ask": []}
        mine = {}
        for r in own_raw.values():
            o = _Own(r.order_id, r.side, ctx.t(i, r.price), int(r.volume))
            own[o.side].append(o)
            mine[(o.side, o.price_t)] = mine.get((o.side, o.price_t), 0) + o.volume
        b = e.get_last_price_book(i)
        bids = [(ctx.t(i, x.price), x.volume - mine.get(("bid", ctx.t(i, x.price)), 0)) for x in b.bids]
        asks = [(ctx.t(i, x.price), x.volume - mine.get(("ask", ctx.t(i, x.price)), 0)) for x in b.asks]
        bids = [x for x in bids if x[1] > 0]
        asks = [x for x in asks if x[1] > 0]
        p = pos.get(i, 0) + int(round(self.extra_delta.get(i, 0.0)))
        plan = {"i": i, "own": own, "want": {"bid": (None, 0), "ask": (None, 0)}, "spread": 0}
        if not bids or not asks or self.pause_until.get(i, -1e18) > now:
            return plan
        (bb, bv), (ba, av) = bids[0], asks[0]
        if self.fair == "deep":  # mid of where real size sits: small rival orders cannot drag it around
            fair = (self._depth_px(bids, self.depth_lots) + self._depth_px(asks, self.depth_lots)) / 2.0
        elif self.fair == "micro":
            fair = (bb * av + ba * bv) / (bv + av)
        else:
            fair = (bb + ba) / 2.0
        self.last_fair[i] = ctx.px(i, fair)
        plan["spread"] = ba - bb
        plan.update(fair=fair, bids=bids, asks=asks)
        limit, soft = self.position_limit, self.soft_limit
        if self.end_time is not None and self.wind_down_s:
            left = self.end_time - now
            if left < self.wind_down_s:
                f = max(0.0, left / self.wind_down_s)
                soft = int(soft * f)
        skew = self.skew_per_lot * p
        bid = min(bb + self.inside, math.floor(fair - self.quote_edge - skew + 1e-9))
        ask = max(ba - self.inside, math.ceil(fair + self.quote_edge - skew - 1e-9))
        bid = min(bid, ba - 1)
        ask = max(ask, bb + 1)
        if ask <= bid:
            ask = bid + 1
        bsz = self.size if p < soft else 0
        asz = self.size if p > -soft else 0
        if self.quote_mode == "reduce":  # quotes only work positions off; profit comes from picking off
            bsz = 0 if p >= 0 else bsz
            asz = 0 if p <= 0 else asz
        elif self.quote_mode == "off":
            bsz = asz = 0
        if p > 0 and self.quote_mode != "off":  # reducing side may go bigger, up to the position
            asz = max(asz, min(p, self.size * 2))
        if p < 0 and self.quote_mode != "off":
            bsz = max(bsz, min(-p, self.size * 2))
        real = pos.get(i, 0)  # exchange limits apply to the stock position itself
        bsz = max(0, min(bsz, limit - real))  # our quote on a side replaces the old one, so worst case = limit - pos
        asz = max(0, min(asz, limit + real))
        plan["want"] = {"bid": (bid if bsz else None, bsz), "ask": (ask if asz else None, asz)}
        return plan

    @staticmethod
    def _depth_px(levels, lots):
        """Price where cumulative volume first reaches `lots` (best price first)."""
        cum = 0
        for px, v in levels:
            cum += v
            if cum >= lots:
                return px
        return levels[-1][0]

    def take(self, e, ctx, i, fair, bids, asks, pos, own=None):
        """Measured against OUR price for the stock: fair value minus the inventory skew. When we are long and
        leaning to sell, a cheap offer must be cheaper still before we buy more (and it can never hit our own
        lowered ask, which the exchange would refuse as a self-trade)."""
        done = False
        p_eff = pos.get(i, 0) + int(round(self.extra_delta.get(i, 0.0)))
        ref = fair - self.skew_per_lot * p_eff
        for side, lv in (("bid", asks), ("ask", bids)):
            if not lv:
                continue
            px = lv[0][0]
            opp = [o.price_t for o in (own or {}).get("ask" if side == "bid" else "bid", []) if not o.gone]
            if opp and ((side == "bid" and min(opp) <= px) or (side == "ask" and max(opp) >= px)):
                continue  # our own resting order is in the way: the exchange would refuse a self-trade
            edge = (ref - px) if side == "bid" else (px - ref)
            if edge >= self.take_edge:
                p = pos.get(i, 0)
                room = (self.soft_limit - p) if side == "bid" else (self.soft_limit + p)  # never past the soft limit
                vol = min(self.take_size, lv[0][1], ctx.capacity(i, side, pos), max(0, room))
                if vol > 0 and ctx.ioc(i, side, px, vol, tag="take"):
                    done = True
        return done

    def reconcile(self, ctx, plan):
        i = plan["i"]
        for side in ("bid", "ask"):
            px, vol = plan["want"][side]
            live = [o for o in plan["own"][side] if not o.gone]
            keep = None
            for o in live:
                behind = (px - o.price_t) if side == "bid" else (o.price_t - px)
                if px is not None and keep is None and 0 <= behind <= self.sticky_ticks and o.volume >= max(1, vol // 2):
                    keep = o
                else:
                    ctx.delete(i, o.order_id, tag="requote")
            if px is not None and keep is None and vol > 0:
                ctx.limit_order(i, side, px, vol, tag="quote")
            elif keep is not None and keep.volume > vol > 0:
                ctx.amend(i, keep.order_id, vol, tag="resize")

    # ------------------------------------------------------------------ settings panel
    def live_params(self):
        return {k: getattr(self, k) for k in self.LIVE}
