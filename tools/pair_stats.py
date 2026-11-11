"""Which stocks move together, and would trading the gap between them pay after costs?

  python tools/pair_stats.py logs/<run> [--top 10]

From the recorded books: correlation of 5-second mid changes for every pair of instruments, and for each
pair the typical swing of the (log) price gap compared with the cost of crossing both spreads.
'swing / cost' well above 2 is worth a pairs test in the simulator; below 1 means spreads eat the profit.
"""
import argparse
import math
import os
import statistics
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from tools.news_impact import load, mid_at, mids_by_inst  # noqa: E402


def sample(series, t0, t1, step):
    out, t = [], t0
    while t <= t1:
        out.append(mid_at(series, t))
        t += step
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--step", type=float, default=5.0)
    a = ap.parse_args()
    book = load(a.run, "book")
    mids = mids_by_inst(book)
    spreads = {}
    for r in book:
        if r.get("b") and r.get("a"):
            spreads.setdefault(r["i"], []).append(r["a"][0][0] - r["b"][0][0])
    if not book:
        sys.exit("no book data")
    t0, t1 = min(r["t"] for r in book), max(r["t"] for r in book)
    S = {i: sample(s, t0 + a.step, t1, a.step) for i, s in mids.items()}
    ids = sorted(i for i in S if sum(x is not None for x in S[i]) > 10)
    rows = []
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            A, B = ids[x], ids[y]
            pts = [(p, q) for p, q in zip(S[A], S[B]) if p and q]
            if len(pts) < 12:
                continue
            ra = [math.log(b[0] / a_[0]) for a_, b in zip(pts, pts[1:])]
            rb = [math.log(b[1] / a_[1]) for a_, b in zip(pts, pts[1:])]
            try:
                c = statistics.correlation(ra, rb)
            except Exception:
                continue
            gap = [math.log(p) - math.log(q) for p, q in pts]
            swing = statistics.pstdev(gap)
            cost = (statistics.mean(spreads[A]) / statistics.mean(m for _, m in mids[A])
                    + statistics.mean(spreads[B]) / statistics.mean(m for _, m in mids[B]))
            rows.append((c, A, B, swing, cost))
    rows.sort(reverse=True)
    print(f"{'pair':<14}{'corr of ' + str(int(a.step)) + 's moves':>20}{'gap swing %':>13}{'cost to cross %':>17}{'swing/cost':>12}")
    for c, A, B, sw, co in rows[: a.top]:
        print(f"{A + '/' + B:<14}{c:>20.2f}{100 * sw:>13.3f}{100 * co:>17.3f}{(sw / co if co else 0):>12.2f}")


if __name__ == "__main__":
    main()
