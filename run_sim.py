"""Backtest a strategy in the simulator.

  python run_sim.py --strategy cross_arb --scenario basic --seeds 5
  python run_sim.py --strategy quote_hedge --scenario hard --seeds 5 -p edge=2 -p size=15
  python run_sim.py --strategy quote_hedge --scenario competitive --plot out.png
"""
import argparse
import statistics
import sys
import time

from optisim import attach, build
from optisim.scenarios import SCENARIOS
from strategies import STRATEGIES


def parse_params(items):
    out = {}
    for kv in items or []:
        k, v = kv.split("=", 1)
        try:
            v = int(v)
        except ValueError:
            try:
                v = float(v)
            except ValueError:
                v = {"true": True, "false": False}.get(v.lower(), v)
        out[k] = v
    return out


def run_one(strategy, scenario, seed, minutes, every, params, n_teams=12, exit_mode=None):
    """exit_mode None: mark positions at fair value (no exit cost). 'all' / 'net': close like run_live does."""
    m, pairs = build(scenario, seed, n_teams=n_teams)
    strat = STRATEGIES[strategy](pairs, clock=lambda: m.t, **params) if strategy != "none" else None
    e = attach(m, "us", strat, every) if strat else None
    if strat is None:
        m.add_account("us")
    if strat is not None and hasattr(strat, "end_time"):
        strat.end_time = minutes * 60
    steps = int(minutes * 60 / m.dt)
    for _ in range(steps):
        m.step()
    if e is not None and exit_mode:
        from strategies.common import flatten_all, flatten_net
        m.actors = [x for x in m.actors if getattr(x, "e", None) is not e]  # stop our strategy
        flatten_all(e, list(m.instruments)) if exit_mode == "all" else flatten_net(e, pairs)
        for _ in range(5):
            m.step()
    rep = m.report("us")
    rep["others"] = {n: round(m.pnl(n), 1) for n in m.accounts if n.startswith("team")}
    rep["zero_sum_check"] = round(sum(m.pnl(n) for n in m.accounts), 6)
    return m, rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="cross_arb", choices=list(STRATEGIES) + ["none"])
    ap.add_argument("--scenario", default="basic", choices=list(SCENARIOS))
    ap.add_argument("--teams", type=int, default=12, help="competitor count for --scenario crowded")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--every", type=int, default=2, help="strategy loop period in sim steps (0.1s each)")
    ap.add_argument("-p", "--param", action="append", help="strategy param, e.g. -p edge=2")
    ap.add_argument("--plot", help="save equity curves of the first seed to this png")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    params = parse_params(a.param)

    pnls, t0 = [], time.time()
    first = None
    for s in range(a.seeds):
        m, rep = run_one(a.strategy, a.scenario, s, a.minutes, a.every, params, a.teams)
        first = first or m
        pnls.append(rep["pnl_fair"])
        if not a.quiet:
            print(f"seed {s}: pnl={rep['pnl_fair']:>8} mid={rep['pnl_mid']:>8} dd={rep['max_drawdown']:>6} "
                  f"vol={rep['volume']:>5} ops={rep['ops']:>5} maxDelta={rep['max_abs_net_delta']:>3} "
                  f"endPos={rep['final_positions']} rejects={rep['rejects']} others={rep['others']}")
            assert abs(rep["zero_sum_check"]) < 1e-3, "money leaked: engine bug"
    mean = statistics.mean(pnls)
    sd = statistics.stdev(pnls) if len(pnls) > 1 else 0.0
    print(f"{a.strategy} | {a.scenario} | {params or 'defaults'} | mean pnl {mean:.1f} sd {sd:.1f} "
          f"| {a.seeds} seeds x {a.minutes} min in {time.time() - t0:.1f}s")

    if a.plot and first is not None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4.5))
        for n, acc in first.accounts.items():
            if n == "us" or n.startswith("team"):
                xs = [t / 60 for t, _ in acc.equity_curve]
                ys = [v for _, v in acc.equity_curve]
                ax.plot(xs, ys, label=n, linewidth=2 if n == "us" else 1)
        ax.set_xlabel("minutes")
        ax.set_ylabel("PnL (marked at fair value)")
        ax.set_title(f"{a.strategy} on '{a.scenario}' (seed 0)")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(a.plot, dpi=130)
        print("saved", a.plot)
    return mean


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)
