"""Play one tournament round in the crowded sim with full logging, and file the results.

  python tools/round.py 1 --version v0
Round R uses market seed 100+R (never used for experiments) and 12 rival teams.
Writes rounds/round_RR/{report.md, overview.png, meta.json} and appends rounds/results.jsonl.
Raw logs stay in logs/ (gitignored).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("round", type=int)
    ap.add_argument("--version", default="latest")
    ap.add_argument("--teams", type=int, default=12)
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--note", default="")
    ap.add_argument("--scenario", default="crowded")
    ap.add_argument("--period", type=float, default=0.15, help="our loop period in seconds")
    a = ap.parse_args()
    logdir = os.path.join(BASE, "logs", "rounds")
    before = set(glob.glob(os.path.join(logdir, "*")))
    subprocess.run([sys.executable, os.path.join(BASE, "run_live.py"), "--sim", a.scenario, "--teams", str(a.teams),
                    "--period", str(a.period),
                    "--seed", str(100 + a.round), "--strategy", "evolved", "-p", f"version={a.version}",
                    "--minutes", str(a.minutes), "--logdir", logdir], check=True, stdout=subprocess.DEVNULL)
    run = sorted(set(glob.glob(os.path.join(logdir, "*"))) - before)[-1]
    subprocess.run([sys.executable, os.path.join(BASE, "tools", "analyze_run.py"), run], check=True,
                   stdout=subprocess.DEVNULL)
    out = os.path.join(BASE, "rounds", f"round_{a.round:02d}")
    os.makedirs(out, exist_ok=True)
    for fn in ("report.md", "overview.png", "meta.json"):
        shutil.copy(os.path.join(run, fn), out)
    meta = json.load(open(os.path.join(run, "meta.json")))
    from strategies.evolved import LATEST
    res = {"round": a.round, "version": LATEST if a.version == "latest" else a.version, "seed": 100 + a.round,
           "rank": meta["rank"], "n": meta["n_competitors"],
           "pnl": next(r["pnl"] for r in meta["leaderboard"] if r["name"] == "us"),
           "best_rival": max(r["pnl"] for r in meta["leaderboard"] if r["name"] != "us"),
           "best_rival_name": max((r for r in meta["leaderboard"] if r["name"] != "us"), key=lambda r: r["pnl"])["name"],
           "log_dir": os.path.relpath(run, BASE), "note": a.note, "scenario": a.scenario, "period": a.period}
    with open(os.path.join(BASE, "rounds", "results.jsonl"), "a") as f:
        f.write(json.dumps(res) + "\n")
    print(json.dumps(res))


if __name__ == "__main__":
    sys.path.insert(0, BASE)
    main()
