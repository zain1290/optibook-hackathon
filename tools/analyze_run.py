"""Turn a run folder into report.md + overview.png.

  python tools/analyze_run.py logs/<run>          # newest run if no folder given

Everything is computed from the raw logs, so it also works on a run that crashed.
"""
import bisect
import collections
import glob
import json
import os
import statistics
import sys

HORIZONS = (1.0, 5.0, 30.0)


def load(d, name):
    p = os.path.join(d, f"{name}.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # half-written last line after a crash
    return out


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]


def f(x, d=2):
    return "-" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(f(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


class Books:
    """Top-of-book timeline per instrument, rebuilt from book.jsonl."""

    def __init__(self, rows, tick):
        self.t, self.bbo = collections.defaultdict(list), collections.defaultdict(list)
        self.rows = rows
        for r in rows:
            b = r["b"][0] if r["b"] else None
            a = r["a"][0] if r["a"] else None
            self.t[r["i"]].append(r["t"])
            self.bbo[r["i"]].append((b, a))
        self.tick = tick

    def at(self, i, t):
        k = bisect.bisect_right(self.t[i], t) - 1
        return self.bbo[i][k] if k >= 0 else (None, None)

    def mid(self, i, t):
        b, a = self.at(i, t)
        return None if not (b and a) else (b[0] + a[0]) / 2

    def timeweighted(self, i, t_end):
        """Time-weighted mean spread (ticks), mean top size, share of time with a two-sided book."""
        ts, bb = self.t[i], self.bbo[i]
        sp = sz = both = tot = 0.0
        for k in range(len(ts)):
            dt = (ts[k + 1] if k + 1 < len(ts) else t_end) - ts[k]
            if dt <= 0:
                continue
            tot += dt
            b, a = bb[k]
            if b and a:
                both += dt
                sp += dt * (a[0] - b[0]) / self.tick[i]
                sz += dt * (a[1] + b[1]) / 2
        return (sp / both if both else None, sz / both if both else None, both / tot if tot else None)

    def crossed(self, P, D, t_end):
        """Share of time the dual is crossed against the primary, and the edge (ticks) while crossed."""
        events = sorted([(r["t"], r["i"]) for r in self.rows if r["i"] in (P, D)])
        times = sorted(set(t for t, _ in events))
        tot = cross = 0.0
        edges = []
        for k, t in enumerate(times):
            dt = (times[k + 1] if k + 1 < len(times) else t_end) - t
            (pb, pa), (db, da) = self.at(P, t), self.at(D, t)
            if not (pb and pa and db and da) or dt <= 0:
                continue
            tot += dt
            e = max(db[0] - pa[0], pb[0] - da[0]) / self.tick[D]
            if e > 1e-9:
                cross += dt
                edges.append(e)
        return (100 * cross / tot if tot else None, statistics.mean(edges) if edges else None)


def main():
    if len(sys.argv) > 1:
        d = sys.argv[1].rstrip("/")
    else:
        runs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "*")))
        runs = [r for r in runs if os.path.isdir(r)]
        if not runs:
            sys.exit("no runs in logs/")
        d = runs[-1]
    meta = json.load(open(os.path.join(d, "meta.json")))
    S = {s: load(d, s) for s in ["book", "ticks", "orders", "fills", "own_orders", "state", "instruments",
                                 "metrics", "events"]}
    inst = meta.get("instruments", {})
    tick = {k: float((v or {}).get("tick_size") or 0.1) for k, v in inst.items()}
    pairs = [tuple(p) for p in meta.get("pairs", [])]
    ref = {}
    for P, D in pairs:
        ref[P] = ref[D] = P
    all_t = [r["t"] for s in S.values() for r in s if "t" in r]
    t0 = meta.get("t_start", min(all_t) if all_t else 0)
    t1 = meta.get("t_end", max(all_t) if all_t else 0)
    dur = max(1e-9, t1 - t0)
    books = Books(S["book"], tick)
    R = []

    # ---------------------------------------------------------------- summary
    st = S["state"]
    pnls = [(r["t"], r["pnl"]) for r in st if r.get("pnl") is not None]
    peak, mdd = -1e18, 0.0
    for _, v in pnls:
        peak = max(peak, v)
        mdd = max(mdd, peak - v)
    final = meta.get("final") or (st[-1] if st else {})
    R.append(f"# Run report: {os.path.basename(d)}\n")
    sess = meta.get("session", {})
    R.append(f"- Mode: **{sess.get('mode')}**" + (f" (scenario {sess.get('scenario')}, teams {sess.get('teams')}, "
                                                    f"seed {sess.get('seed')})" if sess.get("mode") == "sim" else ""))
    R.append(f"- Strategy: **{meta.get('strategy') or 'observe only'}**, params {meta.get('params')}, "
             f"loop {meta.get('args', {}).get('period')}s")
    R.append(f"- Duration: {dur / 60:.1f} min, loops {meta.get('loops')}, stop: {meta.get('stop_reason')}, "
             f"errors: {meta.get('errors', sum(e['kind'] == 'error' for e in S['events']))}")
    R.append(f"- Final PnL: **{f(final.get('pnl'))}**, max drawdown {f(mdd)}, final positions {final.get('positions')}")
    R.append(f"- Pairs (primary, dual): {pairs}")
    R.append(f"- Code: {meta.get('env', {}).get('git_commit')} dirty={meta.get('env', {}).get('git_dirty')}, "
             f"optibook {meta.get('env', {}).get('optibook_version')}\n")

    if meta.get("leaderboard"):
        R.append(f"## Leaderboard (sim): we are **{meta['rank']}/{meta['n_competitors']}**\n")
        R.append(table(["rank", "team", "pnl", "volume", "max abs net delta"],
                       [[k + 1, r["name"], r["pnl"], r["volume"], r["max_abs_net_delta"]]
                        for k, r in enumerate(meta["leaderboard"])]))
        R.append("")

    # ---------------------------------------------------------------- settings timeline
    sets = [e for e in S["events"] if e["kind"] in ("settings", "paused_by_settings", "resumed_by_settings",
                                                     "manual_flatten", "instrument_changed", "stream_disabled")]
    if sets:
        R.append("## Settings and state changes\n")
        R.append(table(["t (s)", "event", "detail"],
                       [[round(e["t"] - t0, 1), e["kind"], json.dumps(e.get("changes") or e.get("after")
                                                                       or e.get("stream") or "")[:120]] for e in sets]))
        R.append("")

    # ---------------------------------------------------------------- market
    R.append("## Market\n")
    ticks_by = collections.defaultdict(list)
    for t in S["ticks"]:
        ticks_by[t["i"]].append(t)
    rows = []
    for i in sorted(inst):
        sp, sz, two = books.timeweighted(i, t1)
        tv = sum(int(t.get("volume") or 0) for t in ticks_by[i])
        mids = [(t, books.mid(i, t)) for t in books.t[i]]
        mv = [b[1] - a[1] for a, b in zip(mids, mids[1:]) if a[1] is not None and b[1] is not None]
        rows.append([i, tick.get(i), sp, sz, None if two is None else 100 * two,
                     len(ticks_by[i]) / (dur / 60), tv / (dur / 60),
                     statistics.pstdev(mv) / tick[i] if len(mv) > 2 else None])
    R.append(table(["instrument", "tick", "spread (ticks, time-wtd)", "top size", "% time two-sided",
                    "trades/min", "volume/min", "mid change sd (ticks/update)"], rows))
    R.append("")
    if pairs:
        R.append(table(["pair", "% time dual crossed vs primary", "mean edge when crossed (ticks)"],
                       [[f"{P}/{D}", *books.crossed(P, D, t1)] for P, D in pairs]))
        R.append("")

    # counterparties
    if any("buyer" in t for t in S["ticks"]):
        vol = collections.Counter()
        aggr = collections.Counter()
        for t in S["ticks"]:
            v = int(t.get("volume") or 0)
            for who in (t.get("buyer"), t.get("seller")):
                if who:
                    vol[(t["i"], who)] += v
            agg = t.get("buyer") if t.get("aggressor_side") == "bid" else t.get("seller")
            if agg:
                aggr[(t["i"], agg)] += v
        names = sorted(set(n for _, n in vol))
        R.append(f"### Counterparties ({len(names)} distinct names seen in public trades)\n")
        top = vol.most_common(25)
        R.append(table(["instrument", "name", "volume", "of which aggressive", "share of instrument volume %"],
                       [[i, n, v, aggr[(i, n)], 100 * v / max(1, 2 * sum(int(t.get("volume") or 0)
                                                                         for t in ticks_by[i]))]
                        for (i, n), v in top]))
        R.append("")
    else:
        R.append("_Public trades carry no buyer/seller names, so counterparties can't be identified._\n")

    # ---------------------------------------------------------------- our orders
    od = S["orders"]
    if od:
        R.append("## Our orders\n")
        by = collections.Counter((o["action"], o.get("tag")) for o in od)
        R.append(table(["action", "tag", "count", "per min"], [[a, t, n, n / (dur / 60)] for (a, t), n in by.most_common()]))
        R.append("")
        rej = collections.Counter(f"{o['action']}: {o.get('reason') or o.get('error')}" for o in od if o.get("ok") is False)
        if rej:
            R.append(table(["reject reason", "count"], rej.most_common()))
            R.append("")
        lat = collections.defaultdict(list)
        for o in od:
            lat[o["action"]].append(o["latency_ms"])
        R.append(table(["action", "latency p50 ms", "p95 ms", "max ms"],
                       [[a, pct(v, .5), pct(v, .95), max(v)] for a, v in lat.items()]))
        ts = sorted(o["t"] for o in od)
        peak_ops, j = 0, 0
        for k in range(len(ts)):
            while ts[k] - ts[j] >= 1.0:
                j += 1
            peak_ops = max(peak_ops, k - j + 1)
        thr = sum((m.get("orders") or {}).get("throttled", 0) for m in S["metrics"])
        R.append(f"\nPeak ops in any 1 s window: **{peak_ops}**, average {len(od) / dur:.2f}/s, "
                 f"client-side throttled: {thr}\n")

    # ---------------------------------------------------------------- fills and markouts
    fl = S["fills"]
    if fl:
        R.append("## Fills: where the money came from\n")
        R.append("Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. "
                 "Markout = same thing measured h seconds later. Positive = good for us.\n")
        agg = collections.defaultdict(lambda: {"n": 0, "vol": 0, "edge": [], "pnl": 0.0,
                                                **{h: [] for h in HORIZONS}})
        for x in fl:
            tag = x.get("tag") or "untagged"
            a = agg[tag]
            a["n"] += 1
            a["vol"] += x["volume"]
            r = ref.get(x["i"], x["i"])
            sign = 1 if x["side"] == "bid" else -1
            m0 = books.mid(r, x["t"])
            if m0 is not None:
                e = sign * (m0 - x["price"]) / tick[x["i"]]
                a["edge"] += [e] * x["volume"]
                a["pnl"] += e * tick[x["i"]] * x["volume"]
            for h in HORIZONS:
                if x["t"] + h <= t1:
                    mh = books.mid(r, x["t"] + h)
                    if mh is not None:
                        a[h] += [sign * (mh - x["price"]) / tick[x["i"]]] * x["volume"]
        mean = lambda v: statistics.mean(v) if v else None
        R.append(table(["tag", "fills", "volume", "edge at fill (ticks/lot)", "markout 1s", "markout 5s",
                        "markout 30s", "edge x volume (currency)"],
                       [[t, a["n"], a["vol"], mean(a["edge"]), mean(a[1.0]), mean(a[5.0]), mean(a[30.0]), a["pnl"]]
                        for t, a in sorted(agg.items(), key=lambda kv: -kv[1]["vol"])]))
        lag = [x["t"] - x["order_t"] for x in fl if x.get("order_t") is not None]
        if lag:
            R.append(f"\nTime from order sent to fill: p50 {f(pct(lag, .5))} s, p95 {f(pct(lag, .95))} s\n")

    # ---------------------------------------------------------------- risk
    if st:
        R.append("## Risk\n")
        maxpos = collections.Counter()
        for r in st:
            for k, v in r["positions"].items():
                maxpos[k] = max(maxpos[k], abs(v))
        nd = collections.defaultdict(list)
        for r in st:
            for k, v in (r.get("net_delta") or {}).items():
                nd[k].append((r["t"], v))
        rows = []
        for k, series in nd.items():
            tot = nz = 0.0
            for (ta, va), (tb, _) in zip(series, series[1:] + [(t1, 0)]):
                tot += tb - ta
                nz += (tb - ta) if va else 0
            rows.append([k, max(abs(v) for _, v in series), 100 * nz / tot if tot else None])
        R.append(table(["instrument", "max abs position"], sorted(maxpos.items())))
        R.append("")
        R.append(table(["pair", "max abs net delta", "% time net delta not 0"], rows))
        R.append("")

    # ---------------------------------------------------------------- errors
    errs = [e for e in S["events"] if e["kind"] == "error"]
    if errs:
        R.append(f"## Errors ({len(errs)})\n")
        for e in errs[:10]:
            R.append(f"- t={e['t'] - t0:.1f}s `{e['where']}`: {e['error']}")
        R.append("")

    # ---------------------------------------------------------------- calibration
    R.append("## Simulator calibration (copy into optisim/scenarios.py)\n")
    for P, D in pairs:
        sp_p, sz_p, _ = books.timeweighted(P, t1)
        sp_d, sz_d, _ = books.timeweighted(D, t1)
        cr, ce = books.crossed(P, D, t1)
        R.append(f"- {P}: spread {f(sp_p)} ticks, top size {f(sz_p, 0)}, trades/min "
                 f"{f(len(ticks_by[P]) / (dur / 60), 1)} | {D}: spread {f(sp_d)} ticks, top size {f(sz_d, 0)}, "
                 f"trades/min {f(len(ticks_by[D]) / (dur / 60), 1)} | crossed {f(cr)}% of time, edge {f(ce)} ticks")

    with open(os.path.join(d, "report.md"), "w") as fh:
        fh.write("\n".join(R) + "\n")
    print("\n".join(R))
    print(f"\nwrote {os.path.join(d, 'report.md')}")
    try:
        plot(d, S, books, pairs, t0, t1)
    except ImportError:
        print("matplotlib not installed: skipped overview.png")


def plot(d, S, books, pairs, t0, t1):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    series = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    st = S["state"]
    insts = sorted({k for r in st for k in r["positions"]})
    n = 2 + len(pairs)
    fig, axes = plt.subplots(n, 1, figsize=(10, 2.4 * n), sharex=True, facecolor=surface)
    xs = lambda ts: [(t - t0) / 60 for t in ts]

    def style(ax, title):
        ax.set_facecolor(surface)
        ax.set_title(title, loc="left", fontsize=10, color=ink)
        ax.grid(axis="y", color=grid, linewidth=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(grid)
        ax.tick_params(colors=ink2, labelsize=8)

    pn = [(r["t"], r["pnl"]) for r in st if r.get("pnl") is not None]
    ax = axes[0]
    if pn:
        ax.plot(xs([t for t, _ in pn]), [v for _, v in pn], color=series[0], linewidth=2)
    style(ax, "PnL")
    ax = axes[1]
    for k, i in enumerate(insts[:8]):
        ys = [r["positions"].get(i, 0) for r in st]
        ax.step(xs([r["t"] for r in st]), ys, where="post", color=series[k], linewidth=2, label=i)
    style(ax, "Positions")
    if insts:
        ax.legend(frameon=False, fontsize=8, labelcolor=ink2, ncol=min(4, len(insts)), loc="lower right", bbox_to_anchor=(1, 1))
    for k, (P, D) in enumerate(pairs):
        ax = axes[2 + k]
        for j, i in enumerate((P, D)):
            pts = [(t, books.mid(i, t)) for t in books.t[i]]
            pts = [(t, m) for t, m in pts if m is not None]
            if pts:
                ax.step(xs([t for t, _ in pts]), [m for _, m in pts], where="post", color=series[j],
                        linewidth=2 if j == 0 else 1.2, label=i)
        fills = [x for x in S["fills"] if x["i"] in (P, D)]
        for side, mk in (("bid", "^"), ("ask", "v")):
            pts = [x for x in fills if x["side"] == side]
            if pts:
                ax.scatter(xs([x["t"] for x in pts]), [x["price"] for x in pts], marker=mk, s=28, color=ink,
                           zorder=3, label=f"our {'buys' if side == 'bid' else 'sells'}",
                           edgecolors=surface, linewidths=1)
        style(ax, f"{P} vs {D}: mid prices and our fills")
        ax.legend(frameon=False, fontsize=8, labelcolor=ink2, ncol=4, loc="lower right", bbox_to_anchor=(1, 1))
    axes[-1].set_xlabel("minutes", color=ink2, fontsize=9)
    fig.tight_layout()
    out = os.path.join(d, "overview.png")
    fig.savefig(out, dpi=130, facecolor=surface)
    print("wrote", out)


if __name__ == "__main__":
    main()
