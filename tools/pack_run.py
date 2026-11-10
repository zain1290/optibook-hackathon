"""Zip run folders to share them (works on Windows/macOS/Linux, no zip CLI needed).

  python tools/pack_run.py logs/<run>              # one run
  python tools/pack_run.py logs/<run1> logs/<run2>  # several runs into one zip
  python tools/pack_run.py --all                    # every run in logs/

Runs analyze_run.py first so report.md and overview.png are inside the zip.
"""
import glob
import os
import subprocess
import sys
import time
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    runs = sorted(d for d in glob.glob(os.path.join(BASE, "logs", "*")) if os.path.isdir(d)) if args == ["--all"] \
        else [a.rstrip("/\\") for a in args]
    for d in runs:
        subprocess.run([sys.executable, os.path.join(BASE, "tools", "analyze_run.py"), d],
                       stdout=subprocess.DEVNULL, check=False)
    name = os.path.basename(runs[0]) if len(runs) == 1 else f"runs_{time.strftime('%Y%m%d-%H%M%S')}"
    out = os.path.join(os.path.dirname(runs[0]), name + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in runs:
            for root, _, files in os.walk(d):
                for fn in files:
                    p = os.path.join(root, fn)
                    z.write(p, os.path.join(os.path.basename(d), os.path.relpath(p, d)))
    print(f"{out}  ({os.path.getsize(out) / 1e6:.1f} MB)  <- send this file")


if __name__ == "__main__":
    main()
