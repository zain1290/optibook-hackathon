"""Describe a scenario's microstructure with no strategy attached, to calibrate against the real thing.

  python tools/market_stats.py --scenario basic --minutes 10
Compare with the same numbers measured live (tools/record_live.py) and tune scenarios.py until close.
"""
import argparse
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from optisim import build  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="basic")
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    m, pairs = build(a.scenario, a.seed)
    stats = {p: dict(sp_p=[], sp_d=[], cross=0, cross_edge=[], n=0) for p in pairs}
    for _ in range(int(a.minutes * 60 / m.dt)):
        m.step()
        for P, D in pairs:
            s = stats[(P, D)]
            pb, pa = m.books[P].best("bid"), m.books[P].best("ask")
            db, da = m.books[D].best("bid"), m.books[D].best("ask")
            if None in (pb, pa, db, da):
                continue
            s["n"] += 1
            s["sp_p"].append(pa - pb)
            s["sp_d"].append(da - db)
            edge = max(db - pa, pb - da)
            if edge > 0:
                s["cross"] += 1
                s["cross_edge"].append(edge)
    for (P, D), s in stats.items():
        n = max(1, s["n"])
        print(f"{P}/{D}: primary spread {statistics.mean(s['sp_p']):.2f} ticks | dual spread "
              f"{statistics.mean(s['sp_d']):.2f} ticks | crossed {100 * s['cross'] / n:.2f}% of steps"
              f" | mean cross edge {statistics.mean(s['cross_edge']) if s['cross_edge'] else 0:.2f} ticks")
        print(f"   trades: {P} {len(m.ticks[P])}, {D} {len(m.ticks[D])} over {a.minutes} min")


if __name__ == "__main__":
    main()
