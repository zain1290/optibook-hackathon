"""Run a strategy against the REAL Optibook exchange (on the day).

  python run_live.py --strategy cross_arb                       # auto-detects X / X_DUAL pairs
  python run_live.py --strategy quote_hedge --pairs ASML:ASML_DUAL -p edge=1 -p size=10
  python run_live.py --flatten                                  # cancel all + close all positions

Ctrl+C stops the loop, cancels resting orders and (by default) flattens positions.
"""
import argparse
import logging
import time

from run_sim import parse_params
from strategies import STRATEGIES
from strategies.common import flatten_all

logging.getLogger("client").setLevel("ERROR")


def detect_pairs(instruments):
    ids = set(instruments)
    pairs = []
    for i in sorted(ids):
        for suffix in ("_DUAL", "_B"):
            base = i[: -len(suffix)] if i.endswith(suffix) else None
            if base and base in ids:
                pairs.append((base, i))
            if base and suffix == "_B" and f"{base}_A" in ids:
                pairs.append((f"{base}_A", i))
    return pairs


def main():
    from optibook.synchronous_client import Exchange  # only available on the hackathon machines

    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="cross_arb", choices=list(STRATEGIES))
    ap.add_argument("--pairs", help="comma list of PRIMARY:DUAL, primary = the LIQUID listing")
    ap.add_argument("--period", type=float, default=0.15, help="seconds between loops")
    ap.add_argument("-p", "--param", action="append")
    ap.add_argument("--flatten", action="store_true", help="just cancel everything and close positions")
    ap.add_argument("--no-flatten-on-exit", action="store_true")
    a = ap.parse_args()

    e = Exchange()
    e.connect()
    instruments = e.get_instruments()
    print("instruments:", {k: (v.tick_size, getattr(v, "paused", None)) for k, v in instruments.items()})
    if a.flatten:
        flatten_all(e, list(instruments))
        print("positions:", e.get_positions())
        return

    pairs = [tuple(p.split(":")) for p in a.pairs.split(",")] if a.pairs else detect_pairs(instruments)
    print("pairs (primary, dual):", pairs, "<- CHECK the primary is the liquid one")
    params = {"hedge_cooldown": 0.2, **parse_params(a.param)}
    strat = STRATEGIES[a.strategy](pairs, **params)

    n, t0 = 0, time.time()
    try:
        while True:
            try:
                strat.step(e)
            except Exception as ex:  # never let one bad response kill the bot
                print("step error:", repr(ex))
            n += 1
            if n % 100 == 0:
                print(f"[{time.time() - t0:7.1f}s] pnl={e.get_pnl():.2f} pos={e.get_positions()}")
            time.sleep(a.period)
    except KeyboardInterrupt:
        print("stopping")
    finally:
        if not a.no_flatten_on_exit:
            flatten_all(e, [i for p in pairs for i in p])
        else:
            for p in pairs:
                for i in p:
                    e.delete_orders(i)
        print("final positions:", e.get_positions(), "pnl:", e.get_pnl())


if __name__ == "__main__":
    main()
