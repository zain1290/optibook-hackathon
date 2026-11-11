"""Recorder: snapshots the whole market and our state every loop. Monitor: rolling metrics + console table."""
import statistics
import time
from collections import Counter, defaultdict, deque

from .core import to_jsonable


def _px(x):
    return round(float(x), 6)


DEEP_LOTS = 200  # same idea as the bot's fair value: ignore small orders, find where real size sits


def deep_mid(bids, asks, lots=DEEP_LOTS):
    """Middle of the prices where at least `lots` are offered (or the deepest level shown).
    Small orders inside the spread (ours, rivals') do not move it, so edge and markouts are measured
    against the same fair value the bot trades on."""
    def at(levels):
        cum = 0
        for px, v in levels:
            cum += v
            if cum >= lots:
                return px
        return levels[-1][0]
    return (at(bids) + at(asks)) / 2


class Monitor:
    """Rolling-window metrics (default 10 s) that answer: how crowded, are we picked off, what pays."""

    HORIZONS = (1.0, 5.0, 30.0)

    def __init__(self, pairs, tick, clock, window=10.0):
        self.pairs, self.tick, self.clock, self.window = pairs, tick, clock, window
        self.ref = {}
        for P, D in pairs:
            self.ref[P] = P
            self.ref[D] = P
        self.bbo = {}  # inst -> (bid, bid_vol, ask, ask_vol)
        self.mid = {}  # reference instrument -> latest mid
        self.news_n = 0
        self.pnl_hist = deque(maxlen=20000)  # (t, pnl) for the hourly Sharpe
        self.mid_hist = defaultdict(lambda: deque(maxlen=5000))
        self.pending = deque()  # (t_fill, sign, px, ref, tag, horizon_idx)
        self.our_quotes = {}  # inst -> {"bid": (px, vol), "ask": (px, vol)}
        self.t_start = clock()
        self.totals = defaultdict(lambda: [0, 0, 0.0])  # tag -> [fills, vol, edge_ticks*vol]
        self._reset()

    def _reset(self):
        self.w_start = self.clock()
        self.spread = defaultdict(list)
        self.crossed = Counter()
        self.samples = Counter()
        self.fills = defaultdict(lambda: [0, 0, 0.0])
        self.markouts = {h: defaultdict(list) for h in self.HORIZONS}
        self.compete = defaultdict(list)  # (inst, side) -> others' volume at or better than our price
        self.mkt = defaultdict(lambda: [0, 0])  # inst -> [trades, volume]
        self.loop_ms = []
        self.rec_ms = []

    # ---- inputs
    def on_book(self, inst, bids, asks, now):
        if bids and asks:
            self.bbo[inst] = (bids[0][0], bids[0][1], asks[0][0], asks[0][1])
            self.spread[inst].append((asks[0][0] - bids[0][0]) / self.tick[inst])
            if self.ref.get(inst, inst) == inst:  # every instrument outside a pair is its own reference
                m = deep_mid(bids, asks) if not self.pairs else (bids[0][0] + asks[0][0]) / 2
                self.mid[inst] = m
                self.mid_hist[inst].append((now, m))
        else:
            self.bbo.pop(inst, None)
        q = self.our_quotes.get(inst)
        if q:
            for side, lv, better in (("bid", bids, lambda p, x: p >= x), ("ask", asks, lambda p, x: p <= x)):
                if side in q:
                    px, ours = q[side]
                    tot = sum(v for p, v in lv if better(p, px))
                    self.compete[(inst, side)].append(max(0, tot - ours))

    def on_pairs(self):
        for P, D in self.pairs:
            if P in self.bbo and D in self.bbo:
                pb, _, pa, _ = self.bbo[P]
                db, _, da, _ = self.bbo[D]
                self.samples[(P, D)] += 1
                if db > pa + 1e-9 or pb > da + 1e-9:
                    self.crossed[(P, D)] += 1

    def on_own_orders(self, inst, orders):
        q = {}
        for _, side, px, vol in orders:
            best = q.get(side)
            if best is None or (px > best[0] if side == "bid" else px < best[0]):
                q[side] = (px, vol)
            elif px == best[0]:
                q[side] = (px, best[1] + vol)
        self.our_quotes[inst] = q

    def on_trade_tick(self, inst, vol):
        self.mkt[inst][0] += 1
        self.mkt[inst][1] += vol

    def on_fill(self, now, inst, side, px, vol, tag):
        ref = self.ref.get(inst, inst)
        sign = 1 if side == "bid" else -1
        mid = self.mid.get(ref)
        tag = tag or "untagged"
        edge = None
        if mid is not None:
            edge = sign * (mid - px) / self.tick[inst]
            for agg in (self.fills[tag], self.totals[tag]):
                agg[2] += edge * vol
            for i, h in enumerate(self.HORIZONS):
                self.pending.append((now + h, sign, px, ref, tag, i, vol, inst))
        for agg in (self.fills[tag], self.totals[tag]):
            agg[0] += 1
            agg[1] += vol
        return mid, edge

    def process_markouts(self, now):
        keep = deque()
        while self.pending:
            item = self.pending.popleft()
            due, sign, px, ref, tag, i, vol, inst = item
            if due > now or ref not in self.mid:
                keep.append(item)
                continue
            self.markouts[self.HORIZONS[i]][tag].append(sign * (self.mid[ref] - px) / self.tick[inst])
        self.pending = keep

    # ---- output
    def emit(self, now, pnl, positions, proxy, pnl_prev):
        self.process_markouts(now)
        dur = max(1e-9, now - self.w_start)
        row = {"t": round(now, 3), "elapsed": round(now - self.t_start, 1), "window_s": round(dur, 2),
               "pnl": pnl, "pnl_change": None if pnl is None or pnl_prev is None else round(pnl - pnl_prev, 3),
               "positions": {k: v for k, v in positions.items() if v}, "pairs": {}}
        for P, D in self.pairs:
            pr = {
                "spread_ticks": {i: round(statistics.mean(self.spread[i]), 3) if self.spread[i] else None
                                 for i in (P, D)},
                "crossed_pct": round(100 * self.crossed[(P, D)] / max(1, self.samples[(P, D)]), 2),
                "net_delta": positions.get(P, 0) + positions.get(D, 0),
                "our_quotes": {i: self.our_quotes.get(i, {}) for i in (P, D)},
                "others_at_or_better": {f"{i}:{s}": round(statistics.mean(v), 1)
                                        for (i, s), v in self.compete.items() if v and i in (P, D)},
                "market_trades": {i: self.mkt[i] for i in (P, D)},
                "mid": self.mid.get(P),
            }
            hist = self.mid_hist[P]
            moves = [b[1] - a[1] for a, b in zip(list(hist)[-200:], list(hist)[-199:])]
            pr["mid_vol_ticks"] = round(statistics.pstdev(moves) / self.tick[P], 3) if len(moves) > 2 else None
            row["pairs"][f"{P}/{D}"] = pr
        paired = {x for p in self.pairs for x in p}
        row["instruments"] = {}
        for i in sorted(set(self.tick) - paired):
            hist = list(self.mid_hist[i])[-200:]
            moves = [b[1] - a[1] for a, b in zip(hist, hist[1:])]
            row["instruments"][i] = {
                "spread_ticks": round(statistics.mean(self.spread[i]), 3) if self.spread[i] else None,
                "mid": self.mid.get(i), "position": positions.get(i, 0),
                "our_quotes": self.our_quotes.get(i, {}),
                "others_at_or_better": {s: round(statistics.mean(v), 1) for (j, s), v in self.compete.items()
                                        if v and j == i},
                "market_trades": self.mkt[i],
                "mid_vol_ticks": round(statistics.pstdev(moves) / self.tick[i], 3) if len(moves) > 2 else None,
            }
        if pnl is not None:
            self.pnl_hist.append((now, pnl))
        from optisim.market import hourly_sharpe
        row["hourly_sharpe"] = hourly_sharpe(list(self.pnl_hist), bucket=max(10.0, self.window))
        row["cash_delta"] = round(sum(positions.get(i, 0) * (self.mid.get(i) or 0) for i in positions), 2)
        row["news_posts"] = self.news_n
        row["fills"] = {tag: {"n": f[0], "vol": f[1], "edge_ticks_per_lot": round(f[2] / f[1], 3) if f[1] else None}
                        for tag, f in self.fills.items()}
        row["markout_ticks"] = {f"{int(h)}s": {tag: round(statistics.mean(v), 3) for tag, v in d.items() if v}
                                for h, d in self.markouts.items()}
        row["orders"] = dict(proxy.order_counts)
        row["ops_per_sec"] = round(sum(proxy.order_counts[a] for a in proxy.ORDER_METHODS) / dur, 2)
        row["latency_ms"] = {k: {"n": s[0], "avg": round(s[1] / s[0], 2), "max": round(s[2], 2)}
                             for k, s in proxy.call_stats.items() if s[0]}
        row["loop_ms"] = {"strategy_avg": round(statistics.mean(self.loop_ms), 2) if self.loop_ms else None,
                          "strategy_max": round(max(self.loop_ms), 2) if self.loop_ms else None,
                          "recorder_avg": round(statistics.mean(self.rec_ms), 2) if self.rec_ms else None,
                          "loops": len(self.loop_ms)}
        text = self.format(row)
        proxy.order_counts.clear()
        proxy.call_stats.clear()
        self._reset()
        return row, text

    @staticmethod
    def format(r):
        f = lambda x, d=1: "-" if x is None else f"{x:.{d}f}"
        lines = [f"[{r['elapsed']:7.1f}s] pnl {f(r['pnl'], 2)} ({'+' if (r['pnl_change'] or 0) >= 0 else ''}"
                 f"{f(r['pnl_change'], 2)}/{r['window_s']:.0f}s) | ops {r['ops_per_sec']}/s | "
                 f"rejects {r['orders'].get('rejected', 0)} throttled {r['orders'].get('throttled', 0)} | "
                 f"loop {f(r['loop_ms']['strategy_avg'])}ms"]
        if r.get("instruments"):
            act = {i: v for i, v in r["instruments"].items() if v["position"] or v["our_quotes"]}
            lines.append("  stocks: " + " | ".join(
                f"{i} spr {f(v['spread_ticks'])} pos {v['position']}" for i, v in list(r["instruments"].items())[:12]))
            if r.get("hourly_sharpe") is not None:
                lines.append(f"  hourly sharpe {r['hourly_sharpe']} | cash delta {r['cash_delta']} | news {r['news_posts']}")
        for name, p in r["pairs"].items():
            P, D = name.split("/")
            q = p["our_quotes"].get(D, {})
            ob = p["others_at_or_better"]
            lines.append(f"  {name}: spread P {f(p['spread_ticks'][P])} D {f(p['spread_ticks'][D])} ticks | "
                         f"crossed {p['crossed_pct']}% | net delta {p['net_delta']} | vol {f(p['mid_vol_ticks'], 2)} t/sample")
            lines.append(f"     our quotes D bid {q.get('bid', '-')} ask {q.get('ask', '-')} | others at/better "
                         f"bid {ob.get(D + ':bid', '-')} ask {ob.get(D + ':ask', '-')} | mkt trades "
                         f"P {p['market_trades'][P][0]} D {p['market_trades'][D][0]}")
        if r["fills"]:
            lines.append("  fills: " + " | ".join(f"{t} {v['n']}x/{v['vol']} edge {f(v['edge_ticks_per_lot'], 2)}t"
                                                  for t, v in r["fills"].items()))
        mk = {h: d for h, d in r["markout_ticks"].items() if d}
        if mk:
            lines.append("  markout (ticks, + good): " + " | ".join(
                f"{h} " + ",".join(f"{t} {v:+.2f}" for t, v in d.items()) for h, d in mk.items()))
        if r["positions"]:
            lines.append(f"  positions {r['positions']}")
        return "\n".join(lines)


class Recorder:
    """Pulls everything observable from the exchange each loop and writes it to the run folder."""

    def __init__(self, e, proxy, run, pairs, clock, depth=10, state_period=1.0, inst_period=2.0,
                 metrics_period=10.0, printer=print, poll_every=3):
        self.e, self.proxy, self.run, self.clock = e, proxy, run, clock
        self.depth, self.state_period, self.inst_period = depth, state_period, inst_period
        self.metrics_period, self.printer = metrics_period, printer
        self.inst = e.get_instruments()
        self.ids = sorted(self.inst)
        tick = {i: float(getattr(v, "tick_size", 0.1) or 0.1) for i, v in self.inst.items()}
        self.monitor = Monitor(pairs, tick, clock)
        self.last_book, self.last_own, self.last_state, self.last_inst = {}, {}, None, None
        self.t_state = self.t_inst = -1e18
        self.t_metrics = clock()
        self.pnl_prev = None
        self.disabled = set()
        self._seen = {}
        self.poll_every = max(1, int(poll_every))  # trades / ticks are fetched every N loops: nothing is lost,
        self._n = 0                                 # the exchange hands over everything since the last poll
        self._write_instruments(force=True)

    def _safe(self, name, fn, *a):
        if name in self.disabled:
            return None
        try:
            return fn(*a)
        except AttributeError as ex:
            self.disabled.add(name)
            self.run.event("stream_disabled", stream=name, error=repr(ex))
        except Exception as ex:
            self.run.error(f"recorder.{name}", ex)
        return None

    def _poll_or_diff(self, poll_name, hist_name, i):
        """Prefer poll_new_*(i); if the client has no such method, diff the *_history(i) call instead."""
        src = self.proxy if hasattr(self.proxy, "begin_loop") else self.e  # counted in the call statistics
        if poll_name not in self.disabled:
            out = self._safe(poll_name, getattr(src, poll_name, None) or self._missing(poll_name), i)
            if poll_name not in self.disabled:
                return out or []
        hist = self._safe(hist_name, getattr(src, hist_name, None) or self._missing(hist_name), i) or []
        seen = self._seen.setdefault((hist_name, i), set())
        new = []
        for x in hist:
            k = repr(to_jsonable(x))
            if k not in seen:
                seen.add(k)
                new.append(x)
        return new

    @staticmethod
    def _missing(name):
        def f(*a):
            raise AttributeError(f"client has no {name}")
        return f

    def _write_instruments(self, force=False):
        inst = self._safe("get_instruments", self.e.get_instruments)
        if inst is None:
            return
        self.inst = inst
        snap = to_jsonable(inst)
        if force or snap != self.last_inst:
            self.run.write("instruments", {"instruments": snap})
            if self.last_inst is not None:
                for k, v in snap.items():
                    old = (self.last_inst or {}).get(k)
                    if old != v:
                        self.run.event("instrument_changed", i=k, before=old, after=v)
            self.last_inst = snap

    def snapshot(self, loop_ms=None, force_poll=False):
        t0 = time.perf_counter()
        now = self.clock()
        mon = self.monitor
        if loop_ms is not None:
            mon.loop_ms.append(loop_ms)
        self._n += 1
        poll = force_poll or self._n % self.poll_every == 0
        src = self.proxy if hasattr(self.proxy, "begin_loop") else self.e  # shared one-loop cache
        for i in self.ids:
            b = self._safe("get_last_price_book", src.get_last_price_book, i)
            if b is not None:
                bids = [(_px(pv.price), int(pv.volume)) for pv in list(b.bids)[: self.depth]]
                asks = [(_px(pv.price), int(pv.volume)) for pv in list(b.asks)[: self.depth]]
                key = (tuple(bids), tuple(asks))
                if key != self.last_book.get(i):
                    self.last_book[i] = key
                    self.run.write("book", {"t": round(now, 4), "i": i, "b": bids, "a": asks})
                mon.on_book(i, bids, asks, now)
            for tk in (self._poll_or_diff("poll_new_trade_ticks", "get_trade_tick_history", i) if poll else []):
                row = to_jsonable(tk)
                row = row if isinstance(row, dict) else {"raw": row}
                row.update({"t": round(now, 4), "i": i})
                self.run.write("ticks", row)
                mon.on_trade_tick(i, int(getattr(tk, "volume", 0) or 0))
            for tr in (self._poll_or_diff("poll_new_trades", "get_trade_history", i) if poll else []):
                oid = getattr(tr, "order_id", None)
                info = self.proxy.order_info.get(oid, {})
                side, px, vol = getattr(tr, "side", None), _px(tr.price), int(tr.volume)
                mid, edge = mon.on_fill(now, i, side, px, vol, info.get("tag"))
                self.run.write("fills", {"t": round(now, 4), "i": i, "order_id": oid, "side": side, "price": px,
                                         "volume": vol, "tag": info.get("tag"), "order_type": info.get("order_type"),
                                         "order_price": info.get("price"), "order_t": info.get("t"),
                                         "ref_mid": mid, "edge_ticks": None if edge is None else round(edge, 3),
                                         "raw": to_jsonable(tr)})
            oo = self._safe("get_outstanding_orders", src.get_outstanding_orders, i)
            if oo is not None:
                own = sorted((int(o.order_id), o.side, _px(o.price), int(o.volume)) for o in oo.values())
                if own != self.last_own.get(i):
                    self.last_own[i] = own
                    self.run.write("own_orders", {"t": round(now, 4), "i": i, "orders": own})
                    mon.on_own_orders(i, own)
        mon.on_pairs()
        reader = getattr(self.proxy, "news_for_recorder", None)
        if reader is not None:
            for post in self._safe("news", reader) or []:
                mon.news_n += 1
                self.run.event("news_seen", post=to_jsonable(post),
                               mids={i: m for i, m in mon.mid.items()})
        if now - self.t_state >= self.state_period:
            self.write_state(now)
        if now - self.t_inst >= self.inst_period:
            self.t_inst = now
            self._write_instruments()
        mon.rec_ms.append((time.perf_counter() - t0) * 1000)
        if now - self.t_metrics >= self.metrics_period:
            self.emit_metrics(now)
        self.run.maybe_flush()

    def write_state(self, now, force=False):
        pos = self._safe("get_positions", self.e.get_positions) or {}
        pnl = self._safe("get_pnl", self.e.get_pnl)
        pnl = None if pnl is None else round(float(pnl), 4)
        cash = self._safe("get_cash", getattr(self.e, "get_cash", None) or self._missing("get_cash"))
        state = {"positions": {k: int(v) for k, v in pos.items()}, "pnl": pnl,
                 "cash": None if cash is None else round(float(cash), 4),
                 "net_delta": {f"{P}/{D}": pos.get(P, 0) + pos.get(D, 0) for P, D in self.monitor.pairs}}
        if force or state != self.last_state or now - self.t_state >= 5 * self.state_period:
            self.run.write("state", {"t": round(now, 4), **state})
        self.last_state, self.t_state = state, now
        return state

    def emit_metrics(self, now):
        st = self.last_state or {"positions": {}, "pnl": None}
        row, text = self.monitor.emit(now, st["pnl"], st["positions"], self.proxy, self.pnl_prev)
        self.pnl_prev = st["pnl"]
        self.t_metrics = now
        self.run.write("metrics", row)
        self.printer(text)
