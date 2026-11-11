"""Do news posts move prices? Run this on a recorded run folder before switching news trading on.

  python tools/news_impact.py logs/<run>

For every post: which instruments it names, its sentiment score (strategies/news.py), and how far each named
instrument's mid moved 1, 5 and 30 seconds later, in ticks, signed by the sentiment (+ = moved the way the
words said). If the 'signed move' averages clearly above the spread, news trading pays (news_trade_size > 0).
"""
import json
import os
import statistics
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
HORIZONS = (1.0, 5.0, 30.0)


def load(d, s):
    p = os.path.join(d, f"{s}.jsonl")
    return [json.loads(x) for x in open(p)] if os.path.exists(p) else []


def mids_by_inst(book):
    out = {}
    for r in book:
        if r.get("b") and r.get("a"):
            out.setdefault(r["i"], []).append((r["t"], (r["b"][0][0] + r["a"][0][0]) / 2))
    return out


def mid_at(series, t):
    last = None
    for ts, m in series:
        if ts > t:
            break
        last = m
    return last


def analyse(d):
    from strategies.news import read_post
    meta = json.load(open(os.path.join(d, "meta.json")))
    tick = {k: float((v or {}).get("tick_size") or 0.1) for k, v in (meta.get("instruments") or {}).items()}
    news, mids = load(d, "news"), mids_by_inst(load(d, "book"))
    rows, signed = [], {h: [] for h in HORIZONS}
    for p in news:
        insts, score, text, _ = read_post(p, sorted(tick))
        t = p.get("t")
        for i in insts:
            s = mids.get(i, [])
            m0 = mid_at(s, t)
            if m0 is None:
                continue
            mv = {}
            for h in HORIZONS:
                mh = mid_at(s, t + h)
                mv[h] = None if mh is None else (mh - m0) / tick.get(i, 0.1)
                if mv[h] is not None and score:
                    signed[h].append(mv[h] * (1 if score > 0 else -1))
            rows.append((round(t, 1), i, score, mv, text[:70]))
    return rows, signed


def report(d):
    rows, signed = analyse(d)
    out = [f"## News impact ({len(rows)} post x instrument pairs)\n"]
    if not rows:
        out.append("_No posts named a traded instrument in this run._\n")
        return "\n".join(out)
    out.append("| t (s) | instrument | sentiment | move 1s | move 5s | move 30s | post |")
    out.append("|---|---|---|---|---|---|---|")
    fmt = lambda x: "-" if x is None else f"{x:+.1f}"
    for t, i, sc, mv, text in rows[:40]:
        out.append(f"| {t} | {i} | {sc:+d} | {fmt(mv[1.0])} | {fmt(mv[5.0])} | {fmt(mv[30.0])} | {text} |")
    out.append("")
    for h in HORIZONS:
        v = signed[h]
        if v:
            out.append(f"- {int(h)}s after a post with a clear sentiment, price moved **{statistics.mean(v):+.2f} ticks** "
                       f"in the direction of the words on average (n={len(v)}, {100 * sum(x > 0 for x in v) / len(v):.0f}% "
                       "of the time the right way)")
    out.append("\nRule of thumb: switch news trading on (news_trade_size 20-50) only if the 5s number is clearly "
               "bigger than half the spread and right more than ~65% of the time.\n")
    return "\n".join(out)


if __name__ == "__main__":
    print(report(sys.argv[1].rstrip("/")))
