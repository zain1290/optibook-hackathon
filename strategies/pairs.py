"""Pairs trading (statistical arbitrage) between two related stocks, e.g. MU/SNDK or NVDA/AMD.

Idea: two companies in the same sector move together. Track the gap between them,
  gap = log(price A) - beta * log(price B)      beta from a rolling regression of log prices,
and its z-score (how many standard deviations the gap is from its recent average).
When z > entry, A is expensive relative to B: sell A, buy B (same money on each side). Close when |z| < exit.

Warning from the simulator: crossing two spreads costs a lot relative to typical gaps. Only switch this on if
the monitor shows a pair whose gap swings by much more than both spreads (see tools/pair_stats.py).
"""
import math
import time
from collections import deque

from .common import Ctx, RateBudget


class PairsTrader:
    name = "pairs"
    LIVE = ("entry_z", "exit_z", "lots", "max_lots", "window")

    def __init__(self, pairs=None, stock_pairs="MU:SNDK,NVDA:AMD,CRWV:NBIS", entry_z=2.5, exit_z=0.5, lots=10,
                 max_lots=60, window=600, min_samples=200, sample_secs=0.5, position_limit=300,
                 max_ops_per_sec=20, clock=None, hedge_cooldown=0.0, budget=None):
        self.clock = clock or time.monotonic
        sp = stock_pairs if not isinstance(stock_pairs, str) else [tuple(x.split(":")) for x in stock_pairs.split(",") if x]
        self.stock_pairs = [tuple(p) for p in sp]
        self.entry_z, self.exit_z, self.lots, self.max_lots = entry_z, exit_z, lots, max_lots
        self.window, self.min_samples, self.sample_secs = window, min_samples, sample_secs
        self.position_limit = position_limit
        self.budget = budget or RateBudget(max_ops_per_sec, self.clock)
        self.ctx = None
        self.hist = {p: deque(maxlen=window) for p in self.stock_pairs}
        self.t_sample = -1e18
        self.state = {}  # pair -> last z, beta
        self.end_time = None

    @property
    def limit(self):
        return self.position_limit

    @staticmethod
    def _mid(e, i):
        b = e.get_last_price_book(i)
        if not b.bids or not b.asks:
            return None
        return (b.bids[0].price + b.asks[0].price) / 2.0

    def step(self, e):
        if self.ctx is None:
            self.ctx = Ctx(e, self.position_limit, self.budget)
        ctx, now = self.ctx, self.clock()
        if now - self.t_sample < self.sample_secs:
            return
        self.t_sample = now
        pos = e.get_positions()
        for A, B in self.stock_pairs:
            if A not in ctx.inst or B not in ctx.inst or ctx.paused(A) or ctx.paused(B):
                continue
            ma, mb = self._mid(e, A), self._mid(e, B)
            if not ma or not mb:
                continue
            h = self.hist[(A, B)]
            h.append((math.log(ma), math.log(mb)))
            if len(h) < self.min_samples:
                continue
            xs, ys = [x[1] for x in h], [x[0] for x in h]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            vx = sum((x - mx) ** 2 for x in xs)
            beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx if vx > 0 else 1.0
            gaps = [y - beta * x for x, y in zip(xs, ys)]
            mu = sum(gaps) / len(gaps)
            sd = (sum((g - mu) ** 2 for g in gaps) / (len(gaps) - 1)) ** 0.5
            if sd <= 0:
                continue
            z = (gaps[-1] - mu) / sd
            self.state[(A, B)] = {"z": round(z, 2), "beta": round(beta, 3)}
            pa = pos.get(A, 0)
            # target: short A when z high, long A when z low; B sized to equal money, opposite sign
            if z > self.entry_z:
                target = -self.max_lots
            elif z < -self.entry_z:
                target = self.max_lots
            elif abs(z) < self.exit_z:
                target = 0
            else:
                target = pa
            step = max(-self.lots, min(self.lots, target - pa))
            if step == 0:
                continue
            tb = -int(round((pa + step) * ma / mb * beta)) - pos.get(B, 0)
            self._trade(e, ctx, A, step, pos)
            self._trade(e, ctx, B, tb, pos)
            ctx.log("pairs", pair=[A, B], z=round(z, 2), beta=round(beta, 3), trade_a=step, trade_b=tb)

    def _trade(self, e, ctx, i, qty, pos):
        if qty == 0:
            return
        side = "bid" if qty > 0 else "ask"
        vol = min(abs(qty), ctx.capacity(i, side, pos))
        b, a = ctx.book(i)
        lv = a if side == "bid" else b
        if vol > 0 and lv:
            ctx.ioc(i, side, lv[0][0], vol, tag="pairs")

    def live_params(self):
        return {k: getattr(self, k) for k in self.LIVE}
