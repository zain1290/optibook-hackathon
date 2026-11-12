"""Logging pipeline tests: the sim run must produce complete, self-consistent logs."""
import glob
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def _run(tmp_path, *args):
    cmd = [sys.executable, os.path.join(BASE, "run_live.py"), "--logdir", str(tmp_path), *args]
    subprocess.run(cmd, check=True, capture_output=True, cwd=BASE)
    return sorted(glob.glob(os.path.join(str(tmp_path), "*")))[-1]


def _rows(d, s):
    return [json.loads(line) for line in open(os.path.join(d, f"{s}.jsonl"))]


def test_full_run_logs_are_complete_and_reconcile(tmp_path):
    d = _run(tmp_path, "--sim", "crowded", "--teams", "4", "--strategy", "quote_hedge", "--minutes", "3", "--exit", "all")
    for s in ["book", "ticks", "orders", "fills", "own_orders", "state", "instruments", "metrics", "events"]:
        assert _rows(d, s), f"{s}.jsonl is empty"
    meta = json.load(open(os.path.join(d, "meta.json")))
    assert meta["stop_reason"] == "time limit" and meta["errors"] == 0
    assert meta["final"]["positions"] == {"ASML": 0, "ASML_DUAL": 0}  # flattened on exit
    fills = _rows(d, "fills")
    assert all(f["tag"] for f in fills), "every fill must be traceable to a reason"
    # cash from our fills marked at the final fair value must equal the reported PnL (flat at the end)
    cash = sum((-1 if f["side"] == "bid" else 1) * f["price"] * f["volume"] for f in fills)
    assert abs(cash - meta["final"]["pnl"]) < 1e-6
    oids = {o.get("order_id") for o in _rows(d, "orders")}
    assert all(f["order_id"] in oids for f in fills)
    subprocess.run([sys.executable, os.path.join(BASE, "tools", "analyze_run.py"), d], check=True,
                   capture_output=True)
    assert os.path.exists(os.path.join(d, "report.md"))


def test_observe_sends_no_orders(tmp_path):
    d = _run(tmp_path, "--sim", "basic", "--observe", "--minutes", "0.5")
    assert _rows(d, "orders") == [] and _rows(d, "book")


def test_pause_setting_stops_trading(tmp_path):
    sf = tmp_path / "s.json"
    sf.write_text('{"pause": true}')
    d = _run(tmp_path / "logs", "--sim", "basic", "--strategy", "quote_hedge", "--minutes", "0.5", "--settings", str(sf))
    assert all(o["action"] == "delete_orders" for o in _rows(d, "orders"))


def test_history_fallback_when_poll_methods_missing(tmp_path):
    from optisim import build
    from optisim.exchange import SimExchange
    from optisim.market import Limits
    from runlog import LoggingExchange, Recorder, Run

    m, pairs = build("basic", 0)
    m.add_account("us", Limits())
    raw = SimExchange(m, "us")

    class OldClient:  # no poll_new_* methods
        def __getattr__(self, n):
            if n.startswith("poll_new"):
                raise AttributeError(n)
            return getattr(raw, n)

    e = OldClient()
    run = Run(str(tmp_path), "t", "sim", lambda: m.t)
    proxy = LoggingExchange(e, run)
    rec = Recorder(e, proxy, run, pairs, lambda: m.t, poll_every=1)
    for _ in range(50):
        m.step()
    proxy.insert_order("ASML", price=200.0, volume=3, side="bid", order_type="ioc")
    rec.snapshot()
    rec.snapshot()
    run.close()
    fills = _rows(run.dir, "fills")
    assert len(fills) >= 1 and sum(f["volume"] for f in fills) == 3  # found once, not duplicated
    assert _rows(run.dir, "ticks")


def test_exit_net_leaves_only_hedged_pairs(tmp_path):
    d = _run(tmp_path, "--sim", "crowded", "--teams", "4", "--strategy", "evolved", "--minutes", "2", "--exit", "net")
    meta = json.load(open(os.path.join(d, "meta.json")))
    assert all(v == 0 for v in meta["final"]["net_delta"].values())


def test_loop_cache_shares_reads_and_drops_them_after_our_orders(tmp_path):
    from optisim import build
    from optisim.exchange import SimExchange
    from optisim.market import Limits
    from runlog import LoggingExchange, Run

    m, _ = build("bonafide_quiet", 0)
    m.add_account("us", Limits())
    e = SimExchange(m, "us")
    run = Run(str(tmp_path), "t", "sim", lambda: m.t)
    p = LoggingExchange(e, run)
    for _ in range(5):
        m.step()
    p.begin_loop()
    b1 = p.get_last_price_book("NVDA")
    assert p.get_last_price_book("NVDA") is b1 and p.cache_hits == 1  # second reader gets the same read
    r = p.insert_order("NVDA", price=b1.bids[0].price - 1.0, volume=1, side="bid")
    assert r.success
    assert len(p.get_outstanding_orders("NVDA")) == 1  # our order dropped the cached (empty) order list
    p.begin_loop()
    assert p.get_last_price_book("NVDA") is not b1  # a new loop reads fresh
    run.close()


def test_enum_sides_from_the_real_client_become_plain_strings(tmp_path):
    from runlog import LoggingExchange, Run
    from runlog.core import norm_side

    class CapnpEnum:  # behaves like the real client's side: equals 'bid' but is not a str
        def __init__(self, v):
            self.v = v

        def __eq__(self, o):
            return o == self.v

        def __hash__(self):
            return hash(("enum", self.v))

    class O:
        def __init__(self, oid, side):
            self.order_id, self.side, self.price, self.volume, self.instrument_id = oid, CapnpEnum(side), 10.0, 1, "X"

    class Fake:
        def get_outstanding_orders(self, i):
            return {1: O(1, "bid"), 2: O(2, "ask")}

        def poll_new_trades(self, i):
            return [O(3, "ask")]

    assert norm_side(CapnpEnum("bid")) == "bid"
    p = LoggingExchange(Fake(), Run(str(tmp_path), "t", "sim", lambda: 0.0))
    p.begin_loop()
    oo = p.get_outstanding_orders("X")
    assert [o.side for o in oo.values()] == ["bid", "ask"] and all(isinstance(o.side, str) for o in oo.values())
    assert {"bid": [], "ask": []}[oo[1].side] == []
    assert p.poll_new_trades("X")[0].side == "ask"
