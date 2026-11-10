"""Evaluate every version of strategies/evolved.py on every market type (held-out seeds 0..N-1).

  python tools/eval_versions.py            # writes rounds/eval_versions.json (used by the notebook)
"""
import argparse
import json
import multiprocessing as mp
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

SCENARIOS = ["crowded", "crowded_sticky", "crowded_tight", "crowded_clones"]


def one(job):
    from run_sim import run_one
    version, scenario, seed, every = job
    m, rep = run_one("evolved", scenario, seed, 10, every, {"version": version}, n_teams=12, exit_mode="net")
    board = {k: m.pnl(k) for k in m.accounts if k == "us" or k.startswith("team")}
    us = board.pop("us")
    hedged = {k: v for k, v in board.items() if m.accounts[k].max_abs_delta <= 40}  # risk-controlled rivals
    return {"version": version, "scenario": scenario, "seed": seed, "pnl": round(us, 2),
            "rank": 1 + sum(v > us for v in board.values()), "n": len(board) + 1,
            "rank_vs_hedged": 1 + sum(v > us for v in hedged.values()),
            "best_rival": round(max(board.values()), 2), "max_abs_net_delta": rep["max_abs_net_delta"],
            "volume": rep["volume"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", default="v0,v1,v2,v3,v4,v5,v6,v8,v10")
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--every", type=int, default=2)
    a = ap.parse_args()
    jobs = [(v, sc, s, a.every) for v in a.versions.split(",") for sc in SCENARIOS for s in range(a.seeds)]
    with mp.Pool(os.cpu_count()) as pool:
        rows = pool.map(one, jobs)
    out = os.path.join(BASE, "rounds", "eval_versions.json")
    with open(out, "w") as f:
        json.dump({"every": a.every, "seeds": a.seeds, "rows": rows}, f)
    print("wrote", out, len(rows), "runs")


if __name__ == "__main__":
    main()
