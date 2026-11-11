"""A crowd of competing teams, modelled on what AI-assisted teams tend to write.

Most teams converge on the same few ideas (dual-listing arb, quote + hedge), with different
parameters and loop speeds. A few ship bugs: here, a bot that quotes but never hedges, then
panic-dumps its position when it hits the limit. That is where free money comes from.
"""
import random

from strategies.common import Ctx, RateBudget
from strategies.cross_arb import CrossArb
from strategies.quote_hedge import QuoteHedge


class UnhedgedQuoter:
    """Buggy team: quotes the dual around the primary mid, forgets to hedge, dumps at the limit."""
    name = "buggy"

    def __init__(self, pairs, position_limit=100, size=10, dump_at=90, dump_slip=6, clock=None):
        self.pairs, self.limit, self.size = pairs, position_limit, size
        self.dump_at, self.slip = dump_at, dump_slip
        self.budget = RateBudget(20, clock) if clock else RateBudget(20)
        self.ctx = None

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
        ctx = self.ctx
        ctx.refresh_instruments()
        for P, D in self.pairs:
            if ctx.paused(P) or ctx.paused(D):
                continue
            pos = e.get_positions()
            pD = pos.get(D, 0)
            db, da = ctx.book(D)
            if abs(pD) >= self.dump_at and db and da:  # panic: dump everything far through the book
                e.delete_orders(D)
                side = "ask" if pD > 0 else "bid"
                px = db[0][0] - self.slip if side == "ask" else da[0][0] + self.slip
                ctx.ioc(D, side, px, abs(pD))
                continue
            pb, pa = ctx.book(P)
            if not (pb and pa):
                continue
            mid = (pb[0][0] + pa[0][0]) // 2
            ctx.delete_all(D)
            ctx.limit_order(D, "bid", mid - 1, min(self.size, ctx.capacity(D, "bid", pos, {})))
            ctx.limit_order(D, "ask", mid + 2, min(self.size, ctx.capacity(D, "ask", pos, {})))


def make_crowd(pairs, n, seed, clock, clone_frac=0.0, clone_version="v8"):
    """Returns [(name, strategy, act_every, phase)] for n competing teams.
    clone_frac: share of teams that run OUR evolved strategy (with jittered settings): the
    'everyone's AI converged on the same idea' case."""
    from strategies.evolved import Evolved
    r = random.Random(seed + 1000)
    out = []
    n_clones = int(round(n * clone_frac))
    for k in range(n):
        u = r.random()
        every = r.choice([1, 2, 3, 5, 10])
        if k < n_clones:
            s = Evolved(pairs, version=clone_version, size=r.choice([5, 10, 15, 20]),
                        min_profit=r.choice([0.3, 0.5, 0.8]), clock=clock)
            out.append((f"team{k:02d}_clone", s, every, r.randrange(every)))
            continue
        if u < 0.6:
            s = QuoteHedge(pairs, edge=r.choice([0, 1, 1, 2]), size=r.choice([5, 10, 20]),
                           penny=r.random() < 0.7, clock=clock)
            kind = "quote_hedge"
        elif u < 0.9:
            s = CrossArb(pairs, min_edge=r.choice([1, 1, 2]), clock=clock)
            kind = "cross_arb"
        else:
            s = UnhedgedQuoter(pairs, size=r.choice([5, 10]), clock=clock)
            kind = "buggy"
        out.append((f"team{k:02d}_{kind}", s, every, r.randrange(every)))
    return out


# ----------------------------------------------------------------------------- Bona Fide (many stocks) crowd
class NaiveStockMaker:
    """Typical first AI-written bot: penny the best bid and ask on every stock, no inventory control,
    dumps everything at the limit. Gives away money when the market trends."""
    name = "naive_mm"

    def __init__(self, position_limit=300, size=20, dump_slip=5, clock=None):
        self.limit, self.size, self.slip = position_limit, size, dump_slip
        self.budget = RateBudget(20, clock) if clock else RateBudget(20)
        self.ctx = None

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
        ctx = self.ctx
        pos = e.get_positions()
        for i in sorted(ctx.inst):
            if ctx.paused(i):
                continue
            p = pos.get(i, 0)
            b, a = ctx.book(i, exclude_own=True)
            if not (b and a):
                continue
            if abs(p) >= self.limit * 0.95:
                ctx.delete_all(i)
                side = "ask" if p > 0 else "bid"
                ctx.ioc(i, side, b[0][0] - self.slip if side == "ask" else a[0][0] + self.slip, abs(p))
                continue
            if a[0][0] - b[0][0] < 3:
                continue
            ctx.delete_all(i)
            ctx.limit_order(i, "bid", b[0][0] + 1, min(self.size, ctx.capacity(i, "bid", pos, {})))
            ctx.limit_order(i, "ask", a[0][0] - 1, min(self.size, ctx.capacity(i, "ask", pos, {})))


class NewsChaser:
    """Reads the news and buys / sells the named stock straight away, holds, then closes later."""
    name = "news_chaser"

    def __init__(self, position_limit=300, size=40, hold_s=20.0, delay_s=0.5, clock=None):
        from strategies.news import read_post
        self._read = read_post
        self.limit, self.size, self.hold, self.delay = position_limit, size, hold_s, delay_s
        self.clock = clock
        self.budget = RateBudget(20, clock) if clock else RateBudget(20)
        self.ctx, self.queue, self.close_at = None, [], {}

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.limit, self.budget)
        ctx, now = self.ctx, self.clock()
        for p in e.poll_new_social_media_feeds():
            insts, score, _, _ = self._read(p, sorted(ctx.inst))
            if score:
                self.queue += [(now + self.delay, i, 1 if score > 0 else -1) for i in insts]
        pos = e.get_positions()
        for item in [q for q in self.queue if q[0] <= now]:
            self.queue.remove(item)
            _, i, sign = item
            b, a = ctx.book(i)
            side = "bid" if sign > 0 else "ask"
            lv = a if sign > 0 else b
            if lv:
                ctx.ioc(i, side, lv[0][0] + (2 if sign > 0 else -2), min(self.size, ctx.capacity(i, side, pos)))
                self.close_at[i] = now + self.hold
        for i, t in list(self.close_at.items()):
            if t <= now and pos.get(i, 0):
                b, a = ctx.book(i)
                p = pos[i]
                if p > 0 and b:
                    ctx.ioc(i, "ask", b[0][0] - 2, p)
                elif p < 0 and a:
                    ctx.ioc(i, "bid", a[0][0] + 2, -p)
                del self.close_at[i]


def make_stock_crowd(n, seed, clock, position_limit=300, clone_frac=0.0):
    """Rival teams for the many-stocks market: mostly market makers like ours with other settings
    (the obvious idea every AI suggests), some naive pennying bots, a few news chasers."""
    from strategies.stock_mm import StockMM
    r = random.Random(seed + 2000)
    out = []
    n_clones = int(round(n * clone_frac))
    for k in range(n):
        u = r.random()
        every = r.choice([1, 2, 3, 5, 10])
        if k < n_clones:
            s = StockMM(position_limit=position_limit, size=r.choice([10, 20, 30]), clock=clock)
            kind = "clone"
        elif u < 0.55:
            s = StockMM(position_limit=position_limit, size=r.choice([5, 10, 20, 40]), inside=r.choice([1, 1, 2]),
                        quote_edge=r.choice([0.5, 1.0, 1.5]), skew_per_lot=r.choice([0.0, 0.005, 0.02]),
                        news_pause=r.choice([0.0, 2.0]), take_edge=r.choice([0, 0, 1]), clock=clock)
            kind = "mm"
        elif u < 0.85:
            s = NaiveStockMaker(position_limit=position_limit, size=r.choice([10, 20, 50]), clock=clock)
            kind = "naive"
        else:
            s = NewsChaser(position_limit=position_limit, size=r.choice([20, 50]), delay_s=r.choice([0.3, 1.0, 3.0]),
                           clock=clock)
            kind = "news"
        out.append((f"team{k:02d}_{kind}", s, every, r.randrange(every)))
    return out
