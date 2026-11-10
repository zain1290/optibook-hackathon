"""Exchange-run bots. They provide liquidity and flow, and bypass team limits.

Other TEAMS are modelled in scenarios.py by running strategy classes through their own SimExchange,
so they face exactly the same limits we do.
"""
import math


class Actor:
    act_every = 1
    phase = 0

    def act(self, m):
        raise NotImplementedError


class LiquidMakerBot(Actor):
    """Primary listing market maker: knows fair value, tight spread, deep book, requotes every step."""

    def __init__(self, name, inst, half_spread_ticks=0.5, levels=3, size=40, act_every=1, keep_queue=False):
        self.name, self.inst = name, inst
        self.hs, self.levels, self.size, self.act_every = half_spread_ticks, levels, size, act_every
        self.keep_queue = keep_queue  # True: leave quotes alone while prices are unchanged (keeps queue spot)
        self._last = None

    def act(self, m):
        if m.instruments[self.inst].paused:
            return
        c = m.fv(self.inst) / m.tick(self.inst)
        bid0, ask0 = math.floor(c - self.hs), math.ceil(c + self.hs)
        if ask0 <= bid0:
            ask0 = bid0 + 1
        if self.keep_queue and self._last == (bid0, ask0):
            sides = {o.side for o in m.resting(self.name, self.inst)}
            if sides == {"bid", "ask"}:
                return
        self._last = (bid0, ask0)
        m.cancel_all(self.name, self.inst, charge=False)
        for i in range(self.levels):
            v = max(1, int(self.size * (1 + i) * m.rng.uniform(0.6, 1.4)))
            m.submit(self.name, self.inst, "bid", bid0 - i, v, charge=False)
            m.submit(self.name, self.inst, "ask", ask0 + i, v, charge=False)


class IlliquidMakerBot(Actor):
    """Dual listing market maker: slow, wide, small, and quotes around a STALE + noisy fair value.
    This staleness is what creates the dual-listing opportunities."""

    def __init__(self, name, inst, lag_steps=20, noise=0.05, half_spread_ticks=4, levels=2, size=8,
                 act_every=10):
        self.name, self.inst = name, inst
        self.lag, self.noise, self.hs = lag_steps, noise, half_spread_ticks
        self.levels, self.size, self.act_every = levels, size, act_every

    def act(self, m):
        if m.instruments[self.inst].paused:
            return
        m.cancel_all(self.name, self.inst, charge=False)
        stock = m.instruments[self.inst].underlying
        est = m.lagged_fv(stock, self.lag) + m.rng.gauss(0, self.noise)
        c = est / m.tick(self.inst)
        bid0, ask0 = math.floor(c - self.hs), math.ceil(c + self.hs)
        for i in range(self.levels):
            v = max(1, int(self.size * m.rng.uniform(0.5, 1.5)))
            m.submit(self.name, self.inst, "bid", bid0 - 2 * i, v, charge=False)
            m.submit(self.name, self.inst, "ask", ask0 + 2 * i, v, charge=False)


class NoiseTakerBot(Actor):
    """Uninformed customer flow: random IOC buys/sells. This is who market makers earn spread from."""

    def __init__(self, name, inst, prob=0.3, max_size=15, sweep_ticks=2):
        self.name, self.inst, self.prob, self.max_size, self.sweep = name, inst, prob, max_size, sweep_ticks

    def act(self, m):
        if m.instruments[self.inst].paused or m.rng.random() > self.prob:
            return
        b = m.books[self.inst]
        side = m.rng.choice(("bid", "ask"))
        best = b.best("ask" if side == "bid" else "bid")
        if best is None:
            return
        px = best + self.sweep if side == "bid" else best - self.sweep
        m.submit(self.name, self.inst, side, px, m.rng.randint(1, self.max_size), ioc=True, charge=False)


class InformedTakerBot(Actor):
    """Fast, informed flow: picks off any quote that is wrong vs true fair value by > threshold.
    Models adverse selection: if your quotes are stale, this is who hits them."""

    def __init__(self, name, inst, threshold_ticks=2, prob=0.2, max_size=10):
        self.name, self.inst, self.thr, self.prob, self.max_size = name, inst, threshold_ticks, prob, max_size

    def act(self, m):
        if m.instruments[self.inst].paused or m.rng.random() > self.prob:
            return
        b = m.books[self.inst]
        fv = m.fv(self.inst) / m.tick(self.inst)
        a, bd = b.best("ask"), b.best("bid")
        if a is not None and a < fv - self.thr:
            m.submit(self.name, self.inst, "bid", a, m.rng.randint(1, self.max_size), ioc=True, charge=False)
        elif bd is not None and bd > fv + self.thr:
            m.submit(self.name, self.inst, "ask", bd, m.rng.randint(1, self.max_size), ioc=True, charge=False)


class StrategyActor(Actor):
    """Runs a strategy's step(e) every `act_every` sim steps (models loop sleep + network latency)."""

    def __init__(self, strategy, exchange, act_every=1, phase=0):
        self.strategy, self.e, self.act_every, self.phase = strategy, exchange, act_every, phase

    def act(self, m):
        self.strategy.step(self.e)
