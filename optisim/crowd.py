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


def make_crowd(pairs, n, seed, clock):
    """Returns [(name, strategy, act_every, phase)] for n competing teams."""
    r = random.Random(seed + 1000)
    out = []
    for k in range(n):
        u = r.random()
        every = r.choice([1, 2, 3, 5, 10])
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
