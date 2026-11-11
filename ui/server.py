"""Control panel for the trading bot. Standard library only, works offline.

  python ui/server.py                 # opens http://127.0.0.1:8050
  python ui/server.py --port 9000 --no-browser
  python ui/server.py --host 0.0.0.0  # reachable from other machines (e.g. a hackathon VM)

Everything it does is a normal run_live.py / tools/*.py call, so logs and results are identical to the CLI.
"""
import argparse
import glob
import inspect
import io
import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
LOGS = os.path.join(BASE, "logs")
UI_DIR = os.path.dirname(os.path.abspath(__file__))

PARAM_HELP = {
    "position_limit": "Max |position| per instrument. Set to the limit in the brief.",
    "max_ops_per_sec": "Our own order-rate cap; keep below the exchange limit.",
    "min_edge": "Ticks a crossed price must offer before the arb trades.",
    "unwind_edge": "Ticks needed for a trade that REDUCES inventory (0 = allowed at no profit).",
    "max_clip": "Max lots per arb trade.",
    "hedge": "Hedge net delta on the primary every loop.",
    "hedge_cooldown": "Seconds to wait after a hedge before hedging again (live: ~0.2).",
    "edge": "quote_hedge / early versions: ticks away from the primary touch.",
    "size": "Lots per quote.",
    "skew_per_lot": "Ticks to shift quotes per lot of dual inventory.",
    "soft_limit": "Stop quoting the side that grows inventory beyond this.",
    "take_min_edge": "min_edge for the built-in arb taker.",
    "penny": "Quote 1 tick better than the best other quote (never past the safe price).",
    "version": "Which evolved version's feature flags to start from.",
    "passive_hedge": "Rest the hedge inside a >=2 tick primary spread instead of crossing.",
    "hedge_timeout": "Seconds before an unfilled passive hedge crosses the spread (IOC).",
    "max_unhedged": "Lots of net delta allowed before hedging immediately with IOC.",
    "sticky_ticks": "Keep a resting quote if it is still safe and within this many ticks of target.",
    "quote_first": "Update quotes before hedging/taking each loop.",
    "arb_single_leg": "Arb takes only the dual leg; the hedger lays off the primary leg.",
    "cost_quote": "Price quotes from fair value +- (hedge cost + min_profit).",
    "passive_cost": "Assumed cost (ticks) of a hedge resting inside the spread.",
    "min_profit": "Extra ticks of profit required per quote on top of hedge cost.",
    "skew_start": "Only skew quotes when |dual position| exceeds this.",
    "touch_secs": "Seconds the hedge first rests AT the touch before moving to mid.",
    "adaptive_touch": "Measure touch-hedge fill rate; skip that step where it doesn't fill.",
    "touch_min_rate": "Min touch fill rate to keep using the touch step.",
    "touch_probe_secs": "Re-test the touch step this often when it is switched off.",
    "arb_cost_aware": "Zero-edge unwinds only when the hedge is ~free (>=2 tick spread).",
    "default_size": "Quote size set by the version (overridden by 'size').",
    "pause": "Pull all quotes and stop trading (positions stay).",
    "flatten": "Cancel everything and close all positions once.",
    "hedge_when_paused": "Keep hedging net delta while paused.",
    "limit": "Position limit used by the strategy.",
    "soft": "Soft limit: stop growing inventory beyond this.",
    "skew": "Ticks of quote shift per lot of inventory.",
    "end_in_secs": "Tell the strategy the session ends in N seconds.",
}


# ----------------------------------------------------------------------------- helpers
def jsonable_default(v):
    return v if isinstance(v, (bool, int, float, str)) or v is None else repr(v)


def strategy_schema():
    from strategies import STRATEGIES
    from strategies.evolved import ALL_FLAGS, FLAGS_BY_VERSION, VERSIONS
    out = {}
    for name, cls in STRATEGIES.items():
        params = []
        for p in inspect.signature(cls.__init__).parameters.values():
            if p.name in ("self", "pairs", "clock") or p.kind in (p.VAR_KEYWORD, p.VAR_POSITIONAL):
                continue
            d = None if p.default is inspect.Parameter.empty else p.default
            params.append({"name": p.name, "default": jsonable_default(d), "help": PARAM_HELP.get(p.name, "")})
        out[name] = {"params": params, "doc": (cls.__doc__ or sys.modules[cls.__module__].__doc__ or "").strip()}
    latest = VERSIONS[FLAGS_BY_VERSION[-1][0]]
    flag_types = {k: type(v).__name__ for k, v in latest.items()}
    for k in ALL_FLAGS:
        flag_types.setdefault(k, "float")
    out["evolved"]["versions"] = {v: VERSIONS[v] for v, _ in FLAGS_BY_VERSION}
    out["evolved"]["version_order"] = [v for v, _ in FLAGS_BY_VERSION]
    out["evolved"]["flag_types"] = flag_types
    out["evolved"]["flag_help"] = {k: PARAM_HELP.get(k, "") for k in ALL_FLAGS}
    return out


def safe_run_dir(d):
    p = os.path.realpath(os.path.join(BASE, d) if not os.path.isabs(d) else d)
    if not p.startswith(os.path.realpath(LOGS) + os.sep) or not os.path.isdir(p):
        raise ValueError("not a run folder under logs/")
    return p


def read_jsonl_tail(path, max_bytes=3_000_000):
    if not os.path.exists(path):
        return []
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
            f.readline()
        data = f.read().decode("utf-8", "replace")
    out = []
    for line in data.splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def downsample(rows, n=600):
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)] + [rows[-1]]


def list_runs():
    runs = []
    for meta_path in glob.glob(os.path.join(LOGS, "*", "meta.json")) + glob.glob(os.path.join(LOGS, "*", "*", "meta.json")):
        d = os.path.dirname(meta_path)
        try:
            meta = json.load(open(meta_path))
        except Exception:
            continue
        final = meta.get("final") or {}
        runs.append({
            "dir": os.path.relpath(d, BASE), "name": os.path.basename(d),
            "group": os.path.relpath(os.path.dirname(d), LOGS),
            "mode": (meta.get("session") or {}).get("mode"), "scenario": (meta.get("session") or {}).get("scenario"),
            "strategy": meta.get("strategy") or ("observe" if (meta.get("args") or {}).get("observe") else None),
            "version": (meta.get("params") or {}).get("version"),
            "pnl": final.get("pnl"), "rank": meta.get("rank"), "n": meta.get("n_competitors"),
            "stop_reason": meta.get("stop_reason"), "errors": meta.get("errors"),
            "has_report": os.path.exists(os.path.join(d, "report.md")),
            "mtime": os.path.getmtime(meta_path),
        })
    return sorted(runs, key=lambda r: -r["mtime"])


# ----------------------------------------------------------------------------- process management
class Job:
    """One child process with captured output."""

    def __init__(self, kind, cmd, info=None):
        self.kind, self.cmd, self.info = kind, cmd, info or {}
        self.started = time.time()
        self.lines = deque(maxlen=3000)
        self.run_dir = None
        creation = {}
        if os.name == "nt":
            creation["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        self.p = subprocess.Popen(cmd, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  bufsize=1, env={**os.environ, "PYTHONUNBUFFERED": "1"}, **creation)
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            if line.startswith("run folder: ") and self.run_dir is None:
                self.run_dir = line[len("run folder: "):].strip()

    def running(self):
        return self.p.poll() is None

    def stop(self, force=False):
        if not self.running():
            return
        if force:
            self.p.kill()
            return
        if self.run_dir and os.path.isdir(self.run_dir):
            open(os.path.join(self.run_dir, "STOP"), "w").close()  # clean stop: exit mode applies, logs close
        else:
            self.p.send_signal(signal.CTRL_C_EVENT if os.name == "nt" else signal.SIGINT)

        def killer():
            time.sleep(20)
            if self.running():
                self.p.kill()
        threading.Thread(target=killer, daemon=True).start()

    def status(self):
        return {"kind": self.kind, "cmd": " ".join(self.cmd[1:]), "info": self.info, "started": self.started,
                "running": self.running(), "returncode": self.p.poll(),
                "run_dir": os.path.relpath(self.run_dir, BASE) if self.run_dir else None,
                "elapsed": round(time.time() - self.started, 1)}


JOBS = {"run": None, "bench": None}
LOCK = threading.Lock()


def build_run_cmd(req):
    mode = req.get("mode", "observe")
    cmd = [sys.executable, "-u", os.path.join(BASE, "run_live.py")]
    if mode == "flatten":
        return cmd + ["--flatten"]
    if mode == "observe":
        cmd.append("--observe")
    else:
        cmd += ["--strategy", req.get("strategy", "evolved")]
        params = dict(req.get("params") or {})
        if req.get("strategy") == "evolved" and req.get("version"):
            params["version"] = req["version"]
        for k, v in params.items():
            if v is None or v == "":
                continue
            cmd += ["-p", f"{k}={v}"]
    if req.get("sim"):
        cmd += ["--sim", req.get("scenario", "crowded"), "--teams", str(int(req.get("teams", 12))),
                "--seed", str(int(req.get("seed", 0))), "--speed", str(float(req.get("speed", 1.0)))]
        cmd += ["--minutes", str(float(req.get("minutes") or 10))]
    elif req.get("minutes"):
        cmd += ["--minutes", str(float(req["minutes"]))]
    if req.get("pairs"):
        cmd += ["--pairs", req["pairs"]]
    for key, flag in (("period", "--period"), ("exit", "--exit"), ("record_every", "--record-every"),
                      ("metrics_every", "--metrics-every")):
        if req.get(key) not in (None, ""):
            cmd += [flag, str(req[key])]
    return cmd


def live_payload():
    job = JOBS["run"]
    out = {"job": job.status() if job else None}
    if not job or not job.run_dir or not os.path.isdir(job.run_dir):
        out["console"] = list(job.lines)[-300:] if job else []
        return out
    d = job.run_dir
    out.update(run_snapshot(d))
    out["console"] = list(job.lines)[-300:]
    return out


def run_snapshot(d):
    meta = {}
    try:
        meta = json.load(open(os.path.join(d, "meta.json")))
    except Exception:
        pass
    state = read_jsonl_tail(os.path.join(d, "state.jsonl"))
    metrics = read_jsonl_tail(os.path.join(d, "metrics.jsonl"), 400_000)
    events = [e for e in read_jsonl_tail(os.path.join(d, "events.jsonl"), 600_000)
              if e.get("kind") not in ("quote_target", "hedge", "arb")]
    fills = read_jsonl_tail(os.path.join(d, "fills.jsonl"), 600_000)
    books = read_jsonl_tail(os.path.join(d, "book.jsonl"), 2_500_000)
    pairs = meta.get("pairs") or []
    insts = sorted({i for p in pairs for i in p})
    mids = {}
    for r in books:
        if r["i"] in insts and r["b"] and r["a"]:
            mids.setdefault(r["i"], []).append([r["t"], (r["b"][0][0] + r["a"][0][0]) / 2])
    settings, spath = None, os.path.join(d, "settings.json")
    if os.path.exists(spath):
        try:
            settings = json.load(open(spath))
        except Exception:
            settings = None
    return {
        "run_dir": os.path.relpath(d, BASE), "meta": meta, "t0": meta.get("t_start"),
        "state": downsample([[r["t"], r.get("pnl"), r.get("positions", {}), r.get("net_delta", {})] for r in state]),
        "metrics": metrics[-1] if metrics else None,
        "metrics_hist": [[m["t"], m.get("pnl")] for m in metrics][-200:],
        "events": events[-60:],
        "fills": [[f["t"], f["i"], f["side"], f["price"], f["volume"], f.get("tag"), f.get("edge_ticks")]
                  for f in fills[-400:]],
        "mids": {k: downsample(v, 500) for k, v in mids.items()},
        "settings": settings,
        "notes": open(os.path.join(d, "notes.md")).read() if os.path.exists(os.path.join(d, "notes.md")) else "",
    }


# ----------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, default=jsonable_default).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, open(os.path.join(UI_DIR, "index.html"), "rb").read(), "text/html; charset=utf-8")
            if u.path in ("/params.json", "/handbook.md"):
                ctype = "application/json" if u.path.endswith(".json") else "text/markdown; charset=utf-8"
                return self._send(200, open(os.path.join(UI_DIR, u.path.lstrip("/")), "rb").read(), ctype)
            if u.path == "/api/meta":
                from optisim.scenarios import TEAM_LIMITS
                return self._send(200, {"strategies": strategy_schema(), "base": BASE, "team_limits": TEAM_LIMITS,
                                        "scenarios": ["basic", "competitive", "hard", "crowded", "crowded_tight",
                                                      "crowded_sticky", "crowded_clones"],
                                        "optibook": optibook_available()})
            if u.path == "/api/live":
                return self._send(200, live_payload())
            if u.path == "/api/runs":
                return self._send(200, list_runs())
            if u.path == "/api/run":
                d = safe_run_dir(q["dir"])
                snap = run_snapshot(d)
                rp = os.path.join(d, "report.md")
                snap["report"] = open(rp).read() if os.path.exists(rp) else None
                snap["has_overview"] = os.path.exists(os.path.join(d, "overview.png"))
                return self._send(200, snap)
            if u.path == "/api/file":
                d = safe_run_dir(q["dir"])
                name = os.path.basename(q["name"])
                p = os.path.join(d, name)
                ctype = {"png": "image/png", "md": "text/markdown", "json": "application/json"}.get(
                    name.rsplit(".", 1)[-1], "text/plain")
                return self._send(200, open(p, "rb").read(), ctype)
            if u.path == "/api/pack":
                d = safe_run_dir(q["dir"])
                subprocess.run([sys.executable, os.path.join(BASE, "tools", "analyze_run.py"), d],
                               cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                    for root, _, files in os.walk(d):
                        for fn in files:
                            z.write(os.path.join(root, fn),
                                    os.path.join(os.path.basename(d), os.path.relpath(os.path.join(root, fn), d)))
                return self._send(200, buf.getvalue(), "application/zip",
                                  {"Content-Disposition": f'attachment; filename="{os.path.basename(d)}.zip"'})
            if u.path == "/api/bench":
                job = JOBS["bench"]
                return self._send(200, {"job": job.status() if job else None,
                                        "output": list(job.lines) if job else []})
            return self._send(404, {"error": "not found"})
        except Exception as ex:
            return self._send(400, {"error": repr(ex)})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            req = self._body()
            if u.path == "/api/start":
                with LOCK:
                    if JOBS["run"] and JOBS["run"].running():
                        return self._send(409, {"error": "a run is already active: stop it first"})
                    cmd = build_run_cmd(req)
                    JOBS["run"] = Job("run", cmd, req)
                return self._send(200, {"ok": True, "cmd": " ".join(cmd[2:])})
            if u.path == "/api/stop":
                job = JOBS["run"]
                if job:
                    job.stop(force=bool(req.get("force")))
                return self._send(200, {"ok": True})
            if u.path == "/api/settings":
                job = JOBS["run"]
                d = safe_run_dir(req["dir"]) if req.get("dir") else (job.run_dir if job else None)
                path = os.path.join(d, "settings.json") if d else None
                if not path or not os.path.exists(path):
                    return self._send(400, {"error": "this run has no settings file (observe mode?)"})
                cur = json.load(open(path))
                cur.update(req.get("changes") or {})
                tmp = path + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(cur, f, indent=2)
                os.replace(tmp, path)  # atomic: the bot never reads a half-written file
                return self._send(200, {"ok": True, "settings": cur})
            if u.path == "/api/notes":
                d = safe_run_dir(req["dir"])
                with open(os.path.join(d, "notes.md"), "w") as f:
                    f.write(req.get("text", ""))
                return self._send(200, {"ok": True})
            if u.path == "/api/analyze":
                d = safe_run_dir(req["dir"])
                r = subprocess.run([sys.executable, os.path.join(BASE, "tools", "analyze_run.py"), d], cwd=BASE,
                                   capture_output=True, text=True)
                return self._send(200 if r.returncode == 0 else 500, {"ok": r.returncode == 0, "stderr": r.stderr[-2000:]})
            if u.path == "/api/bench":
                with LOCK:
                    if JOBS["bench"] and JOBS["bench"].running():
                        return self._send(409, {"error": "a backtest is already running"})
                    variants = [v.strip() for v in str(req.get("variants", "v8 v10")).replace(",", " ").split() if v.strip()]
                    cmd = [sys.executable, "-u", os.path.join(BASE, "tools", "bench.py"), *variants,
                           "--scenario", req.get("scenario", "crowded"), "--seeds", str(int(req.get("seeds", 4))),
                           "--teams", str(int(req.get("teams", 12))), "--every", str(int(req.get("every", 2)))]
                    if req.get("exit"):
                        cmd += ["--exit", req["exit"]]
                    JOBS["bench"] = Job("bench", cmd, req)
                return self._send(200, {"ok": True})
            if u.path == "/api/bench/stop":
                if JOBS["bench"]:
                    JOBS["bench"].stop(force=True)
                return self._send(200, {"ok": True})
            return self._send(404, {"error": "not found"})
        except Exception as ex:
            return self._send(400, {"error": repr(ex)})


def optibook_available():
    try:
        import importlib.util
        return importlib.util.find_spec("optibook") is not None
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8050)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    os.makedirs(LOGS, exist_ok=True)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    url = f"http://{'127.0.0.1' if a.host in ('0.0.0.0', '') else a.host}:{a.port}"
    print(f"control panel: {url}   (Ctrl+C here to quit; running bots are stopped cleanly)")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        job = JOBS["run"]
        if job and job.running():
            print("stopping the running bot cleanly...")
            job.stop()
            for _ in range(40):
                if not job.running():
                    break
                time.sleep(0.5)
        srv.server_close()


if __name__ == "__main__":
    main()
