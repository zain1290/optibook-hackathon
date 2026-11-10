"""Run logging: everything the bot sees and does, as JSON lines in one folder per run.

Folder layout (logs/<YYYYmmdd-HHMMSS>_<strategy>_<mode>/):
  meta.json         run setup: mode, strategy, params, pairs, full instrument reference data, versions
  book.jsonl        order book of EVERY instrument, written whenever it changes  {t,i,b:[[px,vol]..],a:[..]}
  ticks.jsonl       every public trade on the exchange (all fields the client gives, incl. buyer/seller if present)
  orders.jsonl      every insert/amend/delete WE send: request, full response, latency, tag (why)
  fills.jsonl       every fill WE get: tag, order type, fair mid at fill, edge in ticks
  own_orders.jsonl  our resting orders per instrument, whenever they change
  state.jsonl       positions, pnl (and net delta per pair) every state_period seconds and on change
  instruments.jsonl instrument reference data whenever it changes (e.g. paused / unpaused)
  metrics.jsonl     rolling monitor every metrics_period seconds (spreads, crosses, competition, markouts...)
  events.jsonl      decisions (quote targets, arbs, hedges), settings changes, errors with traceback, start/stop
  console.log       everything printed to the terminal
  notes.md          your own observations (template created per run)
"""
import dataclasses
import datetime
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict


# ----------------------------------------------------------------------------- serialisation
def to_jsonable(o, depth=0):
    """Best-effort conversion of any client object (dataclass, __slots__, plain class) to JSON."""
    if o is None or isinstance(o, (bool, int, str)):
        return o
    if isinstance(o, float):
        return round(o, 8)
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    if isinstance(o, dict):
        return {str(k): to_jsonable(v, depth + 1) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [to_jsonable(v, depth + 1) for v in o]
    if depth > 5:
        return repr(o)
    if dataclasses.is_dataclass(o):
        return {f.name: to_jsonable(getattr(o, f.name), depth + 1) for f in dataclasses.fields(o)}
    out = {}
    if hasattr(o, "__dict__"):
        out.update({k: v for k, v in vars(o).items() if not k.startswith("_")})
    for cls in type(o).__mro__:
        for s in getattr(cls, "__slots__", ()):
            if not s.startswith("_") and hasattr(o, s):
                out[s] = getattr(o, s)
    if out:
        return {k: to_jsonable(v, depth + 1) for k, v in out.items()}
    if hasattr(o, "name") and hasattr(o, "value"):  # enums
        return o.name
    return repr(o)


class Jsonl:
    def __init__(self, path):
        self.f = open(path, "a", buffering=1 << 16)
        self.n = 0

    def write(self, row):
        self.f.write(json.dumps(row, separators=(",", ":"), default=repr) + "\n")
        self.n += 1

    def flush(self):
        self.f.flush()

    def close(self):
        self.f.close()


class Tee:
    """Copy stdout into console.log."""

    def __init__(self, path):
        self.f = open(path, "a", buffering=1)
        self.out = sys.stdout

    def write(self, s):
        self.out.write(s)
        self.f.write(s)

    def flush(self):
        self.out.flush()
        self.f.flush()


# ----------------------------------------------------------------------------- run folder
STREAMS = ["book", "ticks", "orders", "fills", "own_orders", "state", "instruments", "metrics", "events"]

NOTES_TEMPLATE = """# Run notes

Fill in while it runs. Anything you see on screen that the bot cannot (leaderboard, brief, announcements).

## Challenge brief (paste the rules: instruments, limits, rate limit, scoring, duration)

## Leaderboard / PnL screenshots or numbers (with time)

## What we changed and why (time - change - reason)

## Observations (other teams, weird prices, pauses, news)
"""


class Run:
    def __init__(self, root, strategy, mode, clock):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        base = os.path.join(root, f"{stamp}_{strategy}_{mode}")
        self.dir, k = base, 1
        while os.path.exists(self.dir):  # never mix two runs in one folder
            k += 1
            self.dir = f"{base}_{k}"
        os.makedirs(self.dir)
        self.clock = clock
        self.w = {s: Jsonl(os.path.join(self.dir, f"{s}.jsonl")) for s in STREAMS}
        with open(os.path.join(self.dir, "notes.md"), "w") as f:
            f.write(NOTES_TEMPLATE)
        self.counters = Counter()
        self._last_flush = time.monotonic()

    def write(self, stream, row):
        row.setdefault("t", round(self.clock(), 4))
        self.w[stream].write(row)

    def event(self, kind, **data):
        self.write("events", {"kind": kind, **to_jsonable(data)})

    def error(self, where, ex):
        self.counters["errors"] += 1
        self.write("events", {"kind": "error", "where": where, "error": repr(ex),
                              "traceback": traceback.format_exc()[-4000:]})

    def write_meta(self, meta):
        with open(os.path.join(self.dir, "meta.json"), "w") as f:
            json.dump(to_jsonable(meta), f, indent=2, default=repr)

    def update_meta(self, **extra):
        p = os.path.join(self.dir, "meta.json")
        try:
            with open(p) as f:
                meta = json.load(f)
        except Exception:
            meta = {}
        meta.update(to_jsonable(extra))
        with open(p, "w") as f:
            json.dump(meta, f, indent=2, default=repr)

    def maybe_flush(self, every=1.0):
        if time.monotonic() - self._last_flush >= every:
            for w in self.w.values():
                w.flush()
            self._last_flush = time.monotonic()

    def close(self):
        for w in self.w.values():
            w.close()


def environment_info(base_dir):
    info = {"python": sys.version.split()[0], "platform": platform.platform(),
            "started_wall": datetime.datetime.now().astimezone().isoformat()}
    try:
        from importlib.metadata import version
        info["optibook_version"] = version("optibook")
    except Exception:
        info["optibook_version"] = None
    try:
        info["git_commit"] = subprocess.check_output(["git", "-C", base_dir, "rev-parse", "--short", "HEAD"],
                                                     stderr=subprocess.DEVNULL).decode().strip()
        info["git_dirty"] = bool(subprocess.check_output(["git", "-C", base_dir, "status", "--porcelain"],
                                                         stderr=subprocess.DEVNULL).strip())
    except Exception:
        info["git_commit"] = None
    return info


# ----------------------------------------------------------------------------- exchange proxy
COUNTER_EVENTS = {"throttled"}  # high-frequency events: counted, not written line by line


class LoggingExchange:
    """Wraps the real (or simulated) Exchange. Logs every order action with latency and response,
    times every other call, and gives strategies tag_next()/log_event() hooks."""

    ORDER_METHODS = ("insert_order", "amend_order", "delete_order", "delete_orders")

    def __init__(self, e, run: Run):
        self._e = e
        self._run = run
        self._next_tag = None
        self.order_info = {}  # order_id -> {inst, side, price, volume, order_type, tag, t}
        self.call_stats = defaultdict(lambda: [0, 0.0, 0.0])  # method -> [n, total_ms, max_ms]
        self.order_counts = Counter()  # action / reject reason counters for the monitor

    # hooks used by strategies.common.Ctx
    def tag_next(self, tag):
        self._next_tag = tag

    def log_event(self, kind, **data):
        if kind in COUNTER_EVENTS:
            self.order_counts[kind] += 1
        else:
            self._run.event(kind, **data)

    def _timed(self, name, fn, *a, **k):
        t0 = time.perf_counter()
        try:
            return fn(*a, **k)
        finally:
            ms = (time.perf_counter() - t0) * 1000
            s = self.call_stats[name]
            s[0] += 1
            s[1] += ms
            s[2] = max(s[2], ms)

    def __getattr__(self, name):
        attr = getattr(self._e, name)
        if not callable(attr) or name in self.ORDER_METHODS:
            return attr
        return lambda *a, **k: self._timed(name, attr, *a, **k)

    def _order(self, action, instrument_id, req, call):
        tag, self._next_tag = self._next_tag, None
        t = self._run.clock()
        t0 = time.perf_counter()
        resp, err = None, None
        try:
            resp = call()
            return resp
        except Exception as ex:
            err = repr(ex)
            raise
        finally:
            ms = (time.perf_counter() - t0) * 1000
            s = self.call_stats[action]
            s[0] += 1
            s[1] += ms
            s[2] = max(s[2], ms)
            if err is not None:
                ok = False
            elif hasattr(resp, "success"):
                ok = bool(resp.success)
            elif isinstance(resp, bool):
                ok = resp
            else:
                ok = None  # client returned something we don't recognise; resp is logged in full
            reason = None
            if ok is False and err is None:
                reason = (getattr(resp, "reason", None) or getattr(resp, "error", None)
                          or getattr(resp, "message", None) or "rejected")
            self.order_counts[action] += 1
            if ok is False:
                self.order_counts["rejected"] += 1
                self.order_counts[f"reject:{reason or err}"] += 1
            row = {"t": round(t, 4), "action": action, "i": instrument_id, "tag": tag, **req,
                   "ok": ok, "reason": reason, "error": err, "latency_ms": round(ms, 3),
                   "resp": to_jsonable(resp)}
            oid = getattr(resp, "order_id", None)
            if action == "insert_order" and oid is not None:
                row["order_id"] = oid
                self.order_info[oid] = {"i": instrument_id, "tag": tag, "t": round(t, 4), **req}
            self._run.write("orders", row)

    def insert_order(self, instrument_id, *, price, volume, side, order_type="limit"):
        req = {"price": price, "volume": volume, "side": side, "order_type": order_type}
        return self._order("insert_order", instrument_id, req,
                           lambda: self._e.insert_order(instrument_id, price=price, volume=volume, side=side,
                                                        order_type=order_type))

    def amend_order(self, instrument_id, *, order_id, volume):
        return self._order("amend_order", instrument_id, {"order_id": order_id, "volume": volume},
                           lambda: self._e.amend_order(instrument_id, order_id=order_id, volume=volume))

    def delete_order(self, instrument_id, *, order_id):
        return self._order("delete_order", instrument_id, {"order_id": order_id},
                           lambda: self._e.delete_order(instrument_id, order_id=order_id))

    def delete_orders(self, instrument_id):
        return self._order("delete_orders", instrument_id, {},
                           lambda: self._e.delete_orders(instrument_id))
