"""Share a run with Claude through GitHub (logs/ itself is not in git).

  python tools/share_run.py               # the newest run
  python tools/share_run.py <run folder>  # a specific one (name or path)

Copies the run into shared_runs/, commits it and pushes. Works on Windows, Mac and Linux.
"""
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(BASE, "logs")


def git(*args):
    print("> git", " ".join(args))
    return subprocess.call(["git", "-C", BASE, *args])


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1].rstrip("/\\")
        src = src if os.path.isdir(src) else os.path.join(LOGS, os.path.basename(src))
    else:
        runs = [os.path.join(LOGS, d) for d in os.listdir(LOGS) if os.path.isfile(os.path.join(LOGS, d, "meta.json"))]
        if not runs:
            sys.exit("no runs in logs/")
        src = max(runs, key=os.path.getmtime)
    name = os.path.basename(src)
    dst = os.path.join(BASE, "shared_runs", name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("STOP", "*.tmp"))
    print(f"copied {name} into shared_runs/")
    git("pull", "--no-edit")
    git("add", os.path.join("shared_runs", name))
    git("commit", "-m", f"run to analyze: {name}")
    if git("push") == 0:
        print(f"\npushed. Tell Claude: 'analyze {name}'")
    else:
        print("\npush failed: use the panel's Past runs > Download zip and drag the zip into the chat instead")


if __name__ == "__main__":
    main()
