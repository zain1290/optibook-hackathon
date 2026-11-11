"""Market scenarios. Start on 'basic', make it work, then prove it survives 'competitive' and 'hard'.

All numbers are guesses at an Optibook-like setup (tick 0.1, position limit 100, ~25 ops/s).
Re-calibrate on the day: record the real books for 5 minutes (tools/record_live.py) and match
spreads, sizes and how often the dual is crossed.
"""
from .bots import (IlliquidMakerBot, InformedTakerBot, LayeredMakerBot, LiquidMakerBot, LotTakerBot, NewsBot,
                   NoiseTakerBot, StrategyActor)
from .exchange import SimExchange
from .market import Limits, Market

TEAM_LIMITS = dict(position_limit=100, max_ops_per_sec=25, self_trade_prevention=True)


def _add_stock(m, name, fv, sigma, jump_prob, jump_sigma, dual_lag=30, informed=False, primary_hs=0.5,
               keep_queue=False):
    P, D = name, f"{name}_DUAL"
    m.add_stock(name, fv, sigma, jump_prob, jump_sigma)
    m.add_instrument(P, name, 0.1, is_primary=True)
    m.add_instrument(D, name, 0.1, is_primary=False)
    for bot in (LiquidMakerBot(f"mm_{P}", P, half_spread_ticks=primary_hs, keep_queue=keep_queue),
                IlliquidMakerBot(f"mm_{D}", D, lag_steps=dual_lag, noise=0.1, half_spread_ticks=2),
                NoiseTakerBot(f"flow_{P}", P, prob=0.4, max_size=15),
                NoiseTakerBot(f"flow_{D}", D, prob=0.08, max_size=8)):
        m.add_account(bot.name)
        m.add_actor(bot)
    if informed:
        bot = InformedTakerBot(f"informed_{D}", D, threshold_ticks=2, prob=0.15)
        m.add_account(bot.name)
        m.add_actor(bot)
    return P, D


def _add_team(m, name, strategy, act_every, phase=0, limits=None):
    m.add_account(name, Limits(**(limits or getattr(m, "team_limits", TEAM_LIMITS))))
    e = SimExchange(m, name)  # the team's ONE connection (a second one would kick this one)
    m.add_actor(StrategyActor(strategy, e, act_every, phase))
    return e


# ----------------------------------------------------------------------------- Bona Fide practice market
# What the visualizer showed on 11 Nov 2026: price, maker half-spread (ticks), maker sizes, sector.
BONA_FIDE = {
    "AMD": (163.0, 2, (3000, 2000, 1000), "chips"),
    "AVGO": (206.7, 2.5, (3000, 2000, 1000), "chips"),
    "NVDA": (124.0, 2, (3000, 2000, 1000), "chips"),
    "MU": (78.4, 1.5, (3000, 2000, 1000), "memory"),
    "SNDK": (53.0, 2.5, (1000, 700, 300), "memory"),
    "CRWV": (143.7, 6.5, (1000, 700, 300), "cloud"),
    "NBIS": (93.3, 4, (1000, 700, 300), "cloud"),
    "VRT": (65.0, 1, (3000, 2000, 1000), "power"),
}
SECTOR_OF = {k: v[3] for k, v in BONA_FIDE.items()}
BONA_FIDE_LIMITS = dict(position_limit=300, max_ops_per_sec=25, self_trade_prevention=True)  # FAQ example: +/-300
BONA_FIDE_SCENARIOS = ("bonafide", "bonafide_quiet", "bonafide_clones", "bonafide_leadlag", "bonafide_informed",
                       "bonafide_derivs")
DUAL_SCENARIOS = ("basic", "competitive", "hard", "crowded", "crowded_tight", "crowded_sticky", "crowded_clones")
SCENARIOS = BONA_FIDE_SCENARIOS + DUAL_SCENARIOS


def build_bonafide(scenario, seed, dt, n_teams):
    """Eight independent stocks, each with one big exchange maker, 20-lot background takers and news.
      bonafide          practice market + n_teams rival teams (default)
      bonafide_quiet    the practice market exactly as seen: no rival teams
      bonafide_clones   half the rival teams run a copy of our stock_mm (everyone's AI wrote the same bot)
      bonafide_leadlag  the thin names' maker reacts late to sector moves (lead-lag / pairs opportunity)
      bonafide_informed a third of the background trades know where price is going; makers are slower
      bonafide_derivs   adds an ETF on the chip stocks, NVDA options and an NVDA future
    """
    from .crowd import make_stock_crowd
    m = Market(dt=dt, seed=seed)
    m.team_limits = BONA_FIDE_LIMITS
    clock = lambda: m.t
    m.add_factor("market", 0.00012)
    for sec in sorted(set(SECTOR_OF.values())):
        m.add_factor(sec, 0.00018)
    thin, deep = [], []
    for name, (px, hs, sizes, sec) in BONA_FIDE.items():
        m.add_stock(name, px, sigma=px * 0.00025, jump_prob=0.0002, jump_sigma=px * 0.004)
        m.stocks[name].loadings = {"market": 1.0, sec: 1.0}
        m.add_instrument(name, name, 0.1, instrument_type="STOCK", price_change_limit=(px * 0.1, 0.1),
                         instrument_group=sec)
        (thin if sizes[0] <= 1000 else deep).append(name)
    informed = scenario == "bonafide_informed"
    lag = 30 if scenario == "bonafide_leadlag" else 0
    every = 5 if informed else 2
    hs = {k: v[1] for k, v in BONA_FIDE.items()}
    sz = {k: v[2] for k, v in BONA_FIDE.items()}
    bots = [LayeredMakerBot("GroovyGrapefruits", deep, {k: hs[k] for k in deep}, {k: sz[k] for k in deep},
                            act_every=every),
            LayeredMakerBot("PrudentPoultry", thin, {k: hs[k] for k in thin}, {k: sz[k] for k in thin},
                            act_every=every, lag_steps=lag),
            LotTakerBot("JazzyJellies", deep, rate_per_sec=0.2, informed=0.33 if informed else 0.0, dt=dt),
            LotTakerBot("LivelyLasagnas", thin, rate_per_sec=0.2, informed=0.33 if informed else 0.0, dt=dt),
            NewsBot("newswire", list(BONA_FIDE), {s: [k for k, v in SECTOR_OF.items() if v == s]
                                                  for s in sorted(set(SECTOR_OF.values()))}, seed=seed, dt=dt)]
    if scenario == "bonafide_derivs":
        bots.append(_add_derivs(m))
    for bot in bots:
        m.add_account(bot.name)
        m.add_actor(bot)
    if scenario != "bonafide_quiet":
        clones = 0.5 if scenario == "bonafide_clones" else 0.0
        for name, strat, ev, ph in make_stock_crowd(n_teams, seed, clock, BONA_FIDE_LIMITS["position_limit"],
                                                    clone_frac=clones):
            _add_team(m, name, strat, ev, ph, limits=BONA_FIDE_LIMITS)
    return m, []


def _add_derivs(m):
    """SEMI_ETF (1 NVDA + 1 AMD + 1 AVGO, divided by 3), NVDA calls/puts at 3 strikes, an NVDA future.
    Expiry 20 sim minutes; on the compressed sim clock (1 sim hour = 1 year) that is 4 months."""
    from .bots import DerivMakerBot
    insts = []
    m.add_instrument("SEMI_ETF", "", 0.1, instrument_type="INDEX_TRACKING_ETF",
                     index_constituents={"NVDA": 1, "AMD": 1, "AVGO": 1}, index_divisor=3.0, etf_cash_comp=0.0,
                     etf_multiplier=1.0, instrument_group="chips")
    insts.append("SEMI_ETF")
    s0 = m.stocks["NVDA"]
    vol = s0.sigma / s0.fv * (3600.0 / m.dt) ** 0.5  # matches how NVDA actually moves in the sim
    for k in (115, 125, 135):
        for kind in ("call", "put"):
            iid = f"NVDA_{k}_{kind[0].upper()}"
            m.add_instrument(iid, "", 0.1, instrument_type="STOCK_OPTION", option_kind=kind, strike=float(k),
                             expiry=1200.0, base_instrument_id="NVDA", interest_rate=0.0)
            m.true_vol[iid] = vol
            insts.append(iid)
    m.add_instrument("NVDA_FUT", "", 0.1, instrument_type="STOCK_FUTURE", expiry=1200.0, base_instrument_id="NVDA",
                     interest_rate=0.05)
    insts.append("NVDA_FUT")
    return DerivMakerBot("OptionOtters", insts, half_spread_ticks=3, size=50, vol_noise=0.05, lag_steps=10)


def build(scenario="basic", seed=0, dt=0.1, n_teams=12):
    """Returns (market, pairs). Add your own strategy with attach().
    'crowded': same market as 'competitive' but with n_teams AI-style competitors (see crowd.py)."""
    from strategies.cross_arb import CrossArb
    from strategies.quote_hedge import QuoteHedge

    if scenario in BONA_FIDE_SCENARIOS:
        return build_bonafide(scenario, seed, dt, n_teams)
    m = Market(dt=dt, seed=seed)
    clock = lambda: m.t
    if scenario == "basic":
        pairs = [_add_stock(m, "ASML", 100.0, 0.02, 0.001, 0.5)]
    elif scenario in ("crowded", "crowded_tight", "crowded_sticky", "crowded_clones"):
        # crowded_tight: primary spread 1 tick, so nobody can hedge inside it (robustness check)
        # crowded_sticky: primary market maker keeps its queue position (no free front-of-queue for us)
        from .crowd import make_crowd
        pairs = [_add_stock(m, "ASML", 100.0, 0.02, 0.0005, 0.5, informed=True,
                            primary_hs=0.0 if scenario == "crowded_tight" else 0.5,
                            keep_queue=scenario == "crowded_sticky")]
        clones = 0.5 if scenario == "crowded_clones" else 0.0  # half the field runs a copy of our v8
        for name, strat, every, phase in make_crowd(pairs, n_teams, seed, clock, clone_frac=clones):
            _add_team(m, name, strat, every, phase)
        return m, pairs
    elif scenario == "competitive":
        pairs = [_add_stock(m, "ASML", 100.0, 0.02, 0.0005, 0.5, informed=True)]
    elif scenario == "hard":
        pairs = [_add_stock(m, "ASML", 100.0, 0.025, 0.002, 0.8, informed=True),
                 _add_stock(m, "NVDA", 50.0, 0.02, 0.002, 0.6, dual_lag=30, informed=True)]
        m.pauses.append(("ASML", 300.0, 360.0))  # primary closed for a minute: can't hedge there
    else:
        raise ValueError(scenario)

    if scenario in ("competitive", "hard"):
        _add_team(m, "team_arb", CrossArb(pairs, min_edge=1, clock=clock), act_every=3, phase=1)
        _add_team(m, "team_maker", QuoteHedge(pairs, edge=2, size=8, penny=False, clock=clock),
                  act_every=5, phase=2)
    return m, pairs


def attach(m, name, strategy, act_every=2):
    return _add_team(m, name, strategy, act_every)
