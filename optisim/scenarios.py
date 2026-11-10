"""Market scenarios. Start on 'basic', make it work, then prove it survives 'competitive' and 'hard'.

All numbers are guesses at an Optibook-like setup (tick 0.1, position limit 100, ~25 ops/s).
Re-calibrate on the day: record the real books for 5 minutes (tools/record_live.py) and match
spreads, sizes and how often the dual is crossed.
"""
from .bots import (IlliquidMakerBot, InformedTakerBot, LiquidMakerBot, NoiseTakerBot,
                   StrategyActor)
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


def _add_team(m, name, strategy, act_every, phase=0):
    m.add_account(name, Limits(**TEAM_LIMITS))
    m.add_actor(StrategyActor(strategy, SimExchange(m, name), act_every, phase))


def build(scenario="basic", seed=0, dt=0.1, n_teams=12):
    """Returns (market, pairs). Add your own strategy with attach().
    'crowded': same market as 'competitive' but with n_teams AI-style competitors (see crowd.py)."""
    from strategies.cross_arb import CrossArb
    from strategies.quote_hedge import QuoteHedge

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
    _add_team(m, name, strategy, act_every)
    return SimExchange(m, name)
