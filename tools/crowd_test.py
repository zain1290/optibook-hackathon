"""How does a strategy hold up as the market fills with competing (AI-style) teams?

  python tools/crowd_test.py --strategy quote_hedge -p edge=1
Prints, per crowd size: our mean PnL, our mean rank among all teams, and PnL by competitor type.
"""
import argparse
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_sim import parse_params, run_one  # noqa: E402
from strategies import STRATEGIES  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="quote_hedge", choices=list(STRATEGIES))
    ap.add_argument("--sizes", default="0,3,6,12,24")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("-p", "--param", action="append")
    a = ap.parse_args()
    params = parse_params(a.param)
    print(f"{a.strategy} {params or ''}")
    print(f"{'teams':>5} {'our pnl':>9} {'rank':>8} {'all teams pnl':>14}  mean pnl by competitor type")
    for n in [int(x) for x in a.sizes.split(",")]:
        ours, ranks, total = [], [], []
        by_kind = defaultdict(list)
        for s in range(a.seeds):
            m, rep = run_one(a.strategy, "crowded", s, a.minutes, a.every, params, n_teams=n)
            teams = {k: m.pnl(k) for k in m.accounts if k.startswith("team") or k == "us"}
            ours.append(teams["us"])
            ranks.append(1 + sum(v > teams["us"] for v in teams.values()))
            total.append(sum(teams.values()))
            for k, v in teams.items():
                if k != "us":
                    by_kind[k.split("_", 1)[1]].append(v)
        kinds = "  ".join(f"{k} {statistics.mean(v):.0f} (n={len(v) / a.seeds:.1f})" for k, v in sorted(by_kind.items()))
        print(f"{n:>5} {statistics.mean(ours):>9.1f} {statistics.mean(ranks):>4.1f}/{n + 1:<3} "
              f"{statistics.mean(total):>14.1f}  {kinds}")


if __name__ == "__main__":
    main()
