"""Control panel: the server starts, serves the page, launches a run and lists it."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get(url, body=None):
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        return json.loads(raw) if r.headers.get("Content-Type", "").startswith("application/json") else raw.decode()


def test_panel_end_to_end():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = subprocess.Popen([sys.executable, os.path.join(BASE, "ui", "server.py"), "--port", str(port), "--no-browser"],
                           cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                meta = _get(url + "/api/meta")
                break
            except OSError:
                time.sleep(0.1)
        assert "evolved" in meta["strategies"] and "v10" in meta["strategies"]["evolved"]["versions"]
        assert "Bot Control Panel" in _get(url + "/")
        _get(url + "/api/start", {"mode": "strategy", "strategy": "evolved", "version": "v8", "params": {"size": 7},
                                  "sim": True, "scenario": "basic", "minutes": 0.5, "speed": 0})
        for _ in range(200):
            live = _get(url + "/api/live")
            if live["job"] and not live["job"]["running"]:
                break
            time.sleep(0.1)
        assert live["job"]["returncode"] == 0
        run = live["run_dir"]
        assert any(r["dir"] == run for r in _get(url + "/api/runs"))
        meta_run = json.load(open(os.path.join(BASE, run, "meta.json")))
        assert meta_run["params"]["size"] == 7 and meta_run["params"]["version"] == "v8"
    finally:
        srv.terminate()
        srv.wait(5)
