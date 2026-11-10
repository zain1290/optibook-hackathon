"""Record the real market for a few minutes (no trading) to calibrate the simulator.

  python tools/record_live.py --minutes 5 --out books.csv

Then compare against:  python tools/market_stats.py --scenario basic
Things to match: primary/dual spread in ticks, % of time the dual is crossed vs the primary,
trades per minute per instrument, typical top-of-book size.
"""
import argparse
import csv
import os
import statistics
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from optibook.synchronous_client import Exchange
    from run_live import detect_pairs

    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--period", type=float, default=0.1)
    ap.add_argument("--out", default="books.csv")
    a = ap.parse_args()

    e = Exchange()
    e.connect()
    inst = e.get_instruments()
    tick = {k: v.tick_size for k, v in inst.items()}
    pairs = detect_pairs(inst)
    best = {}
    n_trades = defaultdict(int)
    stats = defaultdict(lambda: dict(sp=[], cross=0, n=0))
    end = time.time() + a.minutes * 60
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "instrument", "bid", "bid_vol", "ask", "ask_vol", "n_bid_levels", "n_ask_levels"])
        while time.time() < end:
            now = time.time()
            for i in inst:
                b = e.get_last_price_book(i)
                bb, ba = (b.bids[0] if b.bids else None), (b.asks[0] if b.asks else None)
                w.writerow([round(now, 3), i, bb and bb.price, bb and bb.volume, ba and ba.price,
                            ba and ba.volume, len(b.bids), len(b.asks)])
                best[i] = (bb.price if bb else None, ba.price if ba else None)
                if bb and ba:
                    stats[i]["sp"].append((ba.price - bb.price) / tick[i])
                n_trades[i] += len(e.poll_new_trade_ticks(i))
            for P, D in pairs:
                (pb, pa), (db, da) = best.get(P, (None, None)), best.get(D, (None, None))
                if None not in (pb, pa, db, da):
                    stats[(P, D)]["n"] += 1
                    if db > pa or pb > da:
                        stats[(P, D)]["cross"] += 1
            time.sleep(a.period)
    for i in inst:
        sp = stats[i]["sp"]
        print(f"{i}: mean spread {statistics.mean(sp) if sp else float('nan'):.2f} ticks, "
              f"{n_trades[i] / a.minutes:.0f} trades/min")
    for P, D in pairs:
        s = stats[(P, D)]
        print(f"{P}/{D}: crossed {100 * s['cross'] / max(1, s['n']):.2f}% of samples")
    print("saved", a.out)


if __name__ == "__main__":
    main()
