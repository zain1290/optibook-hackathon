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


# ----------------------------------------------------------------------------- Bona Fide practice market
class LayeredMakerBot(Actor):
    """The big exchange maker seen on the Bona Fide visualizer: one account quoting several stocks,
    3 levels per side (e.g. 3000 / 2000 / 1000 lots, best level largest), a fixed number of ticks wide.
    lag_steps > 0 quotes around an OLD fair value (slow to react to news / sector moves)."""

    def __init__(self, name, insts, half_spread_ticks, sizes=(3000, 2000, 1000), act_every=2, lag_steps=0,
                 keep_queue=True, size_jitter=0.02):
        self.name, self.insts = name, list(insts)
        self.hs = half_spread_ticks if isinstance(half_spread_ticks, dict) else {i: half_spread_ticks for i in insts}
        self.sizes = sizes if isinstance(sizes, dict) else {i: sizes for i in insts}
        self.act_every, self.lag, self.keep_queue, self.jit = act_every, lag_steps, keep_queue, size_jitter
        self._last = {}

    def _fair(self, m, inst):
        ins = m.instruments[inst]
        if self.lag and ins.underlying in m.stocks:
            return m.lagged_fv(ins.underlying, self.lag)
        return m.fv(inst)

    def act(self, m):
        for inst in self.insts:
            ins = m.instruments[inst]
            if ins.paused or ins.expired:
                continue
            c = self._fair(m, inst) / m.tick(inst)
            hs = self.hs[inst]
            bid0, ask0 = math.floor(c - hs + 0.5), math.ceil(c + hs - 0.5)
            if ask0 <= bid0:
                ask0 = bid0 + 1
            rest = m.resting(self.name, inst)
            if self.keep_queue and self._last.get(inst) == (bid0, ask0) and {o.side for o in rest} == {"bid", "ask"}:
                continue  # unchanged: keep queue position, only top up what was traded away
            self._last[inst] = (bid0, ask0)
            m.cancel_all(self.name, inst, charge=False)
            for k, size in enumerate(self.sizes[inst]):
                v = max(1, int(size * (1 - m.rng.uniform(0, self.jit))))
                m.submit(self.name, inst, "bid", bid0 - k, v, charge=False)
                m.submit(self.name, inst, "ask", ask0 + k, v, charge=False)


class LotTakerBot(Actor):
    """Background flow seen on the visualizer: fixed 20-lot trades at the best price.
    informed: share of trades that go WITH the next fair-value move instead of random (adverse selection)."""

    def __init__(self, name, insts, rate_per_sec=0.2, lot=20, informed=0.0, dt=0.1):
        self.name, self.insts, self.lot, self.informed = name, list(insts), lot, informed
        self.p = rate_per_sec * dt  # chance per instrument per step

    def act(self, m):
        for inst in self.insts:
            ins = m.instruments[inst]
            if ins.paused or ins.expired or m.rng.random() > self.p:
                continue
            b = m.books[inst]
            bid, ask = b.best("bid"), b.best("ask")
            if bid is None or ask is None:
                continue
            if self.informed and m.rng.random() < self.informed:
                fv = m.fv(inst) / m.tick(inst)
                side = "bid" if fv > (bid + ask) / 2 else "ask"
            else:
                side = m.rng.choice(("bid", "ask"))
            px = ask if side == "bid" else bid
            m.submit(self.name, inst, side, px, self.lot, ioc=True, charge=False)


NEWS_TEMPLATES = {
    1: ["{n} smashes earnings expectations, raises full-year guidance",
        "Reports: hyperscaler signs multi-billion order with {n}",
        "{n} unveils next-gen chip, analysts call it a breakthrough",
        "Analyst upgrades {n} to Strong Buy, sees 30% upside"],
    -1: ["{n} misses revenue estimates, shares slide after hours",
         "Export restrictions could hit {n} sales, sources say",
         "{n} CFO resigns unexpectedly",
         "Short seller publishes report questioning {n} accounting"],
    0: ["{n} to present at industry conference next week",
        "{n} CEO spotted at coffee shop, says 'busy times'",
        "Retail investors keep talking about {n} on forums"],
}
SECTOR_TEMPLATES = {1: "AI spending boom continues: {s} names rally", -1: "Sell-off in {s} as demand fears grow"}


class NewsBot(Actor):
    """Publishes social media posts. Real news moves fair value by `size` (fraction of price), after
    `delay` seconds; noise posts move nothing. Sector posts move every stock in the sector."""

    def __init__(self, name, stocks, sectors=None, every_s=(30, 90), size=(0.005, 0.02), delay=(0.3, 1.5),
                 noise_share=0.35, sector_share=0.2, seed=0, dt=0.1):
        import random
        self.name, self.stocks, self.sectors = name, list(stocks), dict(sectors or {})
        self.every, self.size, self.delay = every_s, size, delay
        self.noise, self.sector_share, self.dt = noise_share, sector_share, dt
        self.r = random.Random(seed + 991)
        self.next_t = self.r.uniform(*every_s) / 3

    def act(self, m):
        if m.t < self.next_t:
            return
        self.next_t = m.t + self.r.uniform(*self.every)
        u = self.r.random()
        if u < self.noise:
            n = self.r.choice(self.stocks)
            m.publish(self.r.choice(NEWS_TEMPLATES[0]).format(n=n), {"source": "newswire"})
            return
        sign = self.r.choice((1, -1))
        if self.sectors and u < self.noise + self.sector_share:
            sec = self.r.choice(sorted(self.sectors))
            mag = self.r.uniform(*self.size) * 0.6
            d = self.r.uniform(*self.delay)
            m.publish(SECTOR_TEMPLATES[sign].format(s=sec), {"source": "newswire"},
                      [(d, st, sign * mag * m.stocks[st].fv) for st in self.sectors[sec]])
            return
        n = self.r.choice(self.stocks)
        mag = self.r.uniform(*self.size)
        m.publish(self.r.choice(NEWS_TEMPLATES[sign]).format(n=n), {"source": "newswire"},
                  [(self.r.uniform(*self.delay), n, sign * mag * m.stocks[n].fv)])


class DerivMakerBot(Actor):
    """Quotes options / futures / ETFs around their true value with a noisy view:
    options at a vol that wanders around the true vol, ETFs and futures off a lagged underlying."""

    def __init__(self, name, insts, half_spread_ticks=3, size=50, levels=2, vol_noise=0.04, lag_steps=10,
                 act_every=5):
        self.name, self.insts, self.hs, self.size, self.levels = name, list(insts), half_spread_ticks, size, levels
        self.vol_noise, self.lag, self.act_every = vol_noise, lag_steps, act_every
        self.vol_bias = {}

    def _theo(self, m, ins):
        from strategies import pricing
        lag = lambda st: m.lagged_fv(st, self.lag) if st in m.stocks else m.fv(st)
        if ins.instrument_type == "INDEX_TRACKING_ETF":
            return pricing.etf_fair_value({k: lag(k) for k in ins.index_constituents}, ins.index_constituents,
                                          ins.index_divisor or 1, ins.etf_cash_comp or 0, ins.etf_multiplier or 1)
        s = lag(ins.base_instrument_id)
        tau = max(0.0, (ins.expiry - m.t) / pricing.SECONDS_PER_YEAR_SIM)
        if ins.instrument_type in ("STOCK_FUTURE", "INDEX_FUTURE"):
            return pricing.future_fair_value(s, ins.interest_rate or 0, tau)
        b = self.vol_bias.get(ins.instrument_id, 0.0)
        b = 0.98 * b + m.rng.gauss(0, self.vol_noise * 0.2)  # slowly wandering vol mispricing
        self.vol_bias[ins.instrument_id] = b
        vol = max(0.02, m.true_vol.get(ins.instrument_id, 0.3) + b)
        return pricing.bs_price(s, ins.strike, tau, vol, ins.interest_rate or 0, ins.option_kind)

    def act(self, m):
        for inst in self.insts:
            ins = m.instruments[inst]
            if ins.paused or ins.expired:
                continue
            m.cancel_all(self.name, inst, charge=False)
            c = self._theo(m, ins) / m.tick(inst)
            bid0, ask0 = math.floor(c - self.hs), math.ceil(c + self.hs)
            for k in range(self.levels):
                if bid0 - k > 0:
                    m.submit(self.name, inst, "bid", bid0 - k, self.size, charge=False)
                m.submit(self.name, inst, "ask", max(ask0 + k, 1), self.size, charge=False)
