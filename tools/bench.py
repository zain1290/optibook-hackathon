"""Benchmark strategy variants on held-out markets (seeds 0..N-1, never used for rounds).

  python tools/bench.py v0 v1                       # compare versions of strategies/evolved.py
  python tools/bench.py v1 v1:passive_hedge=False   # ablate one flag
  python tools/bench.py v2 --teams 24 --seeds 8     # stress: bigger crowd
  python tools/bench.py v2 --scenario hard          # regression check on the 'hard' market
  python tools/bench.py stock_mm stock_mm:min_edge=2 --scenario bonafide   # any strategy: name[:k=v,...]
Prints mean PnL, mean rank, how often we finish 1st, and our PnL minus the best rival's.
"""
import argparse
import multiprocessing as mp
import os
import statistics
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def parse_variant(v):
    if ":" not in v:
        return v, {}
    name, rest = v.split(":", 1)
    over = {}
    for kv in rest.split(","):
        k, val = kv.split("=")
        over[k] = {"True": True, "False": False}.get(val, None)
        if over[k] is None:
            try:
                over[k] = int(val)
            except ValueError:
                try:
                    over[k] = float(val)
                except ValueError:
                    over[k] = val  # text setting, e.g. quote_mode=reduce
    return name, over


def one(job):
    from run_sim import run_one
    from strategies import STRATEGIES
    variant, scenario, seed, teams, minutes, exit_mode, every = job
    name, over = parse_variant(variant)
    if name in STRATEGIES:
        strategy, params = name, over
    else:  # a version of strategies/evolved.py
        strategy, params = "evolved", {"version": name, **over}
    m, rep = run_one(strategy, scenario, seed, minutes, every, params, n_teams=teams, exit_mode=exit_mode)
    board = {k: m.pnl(k) for k in m.accounts if k == "us" or k.startswith("team")}
    us = board["us"]
    rivals = [v for k, v in board.items() if k != "us"]
    rank = 1 + sum(v > us for v in rivals)
    return (variant, us, rank, us - (max(rivals) if rivals else 0), rep["max_abs_net_delta"], len(board),
            rep.get("hourly_sharpe"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="+")
    ap.add_argument("--scenario", default="crowded")
    ap.add_argument("--teams", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--exit", choices=["all", "net"], help="charge the cost of closing positions at the end")
    ap.add_argument("--list", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--every", type=int, default=2, help="our loop period in 0.1 s sim steps")
    a = ap.parse_args()
    jobs = [(v, a.scenario, s, a.teams, a.minutes, a.exit, a.every) for v in a.variants for s in range(a.seeds)]
    with mp.Pool(os.cpu_count()) as pool:
        res = pool.map(one, jobs)
    print(f"{a.scenario}, {a.teams} rival teams, {a.seeds} held-out markets x {a.minutes} min"
          + (f", exit={a.exit}" if a.exit else ""))
    print(f"{'variant':<44} {'mean pnl':>9} {'sd':>6} {'mean rank':>10} {'1st':>5} {'vs best rival':>14} {'max delta':>9}"
          f" {'sharpe/h':>8}")
    for v in a.variants:
        r = [x for x in res if x[0] == v]
        pn = [x[1] for x in r]
        n = r[0][5]
        print(f"{v:<44} {statistics.mean(pn):>9.1f} {statistics.pstdev(pn):>6.1f} "
              f"{statistics.mean(x[2] for x in r):>6.2f}/{n:<3} {sum(x[2] == 1 for x in r):>3}/{len(r):<2}"
              f"{statistics.mean(x[3] for x in r):>14.1f} {max(x[4] for x in r):>9}"
              f" {statistics.mean([x[6] for x in r if x[6] is not None] or [0]):>8.1f}")


if __name__ == "__main__":
    main()
