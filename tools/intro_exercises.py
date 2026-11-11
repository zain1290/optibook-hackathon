"""Optiver's intro exercises (Set A and B) plus the checks we need before trusting the bot, with tiny sizes.

  python tools/intro_exercises.py                 # real exchange (in the Dev Environment), 1 lot
  python tools/intro_exercises.py --sim           # same steps against the simulator
  python tools/intro_exercises.py --probe-rate    # also measure the order rate limit (far-away 1-lot orders)

Everything is logged to logs/<time>_intro_<mode>/ like any other run, and a summary is printed at the end:
instrument fields, tick sizes, the exact error texts the exchange uses, call latency, news format.
Paste the summary into notes.md / the chat: it calibrates the simulator and the bot.
Only ONE program per team can be connected: stop the bot before running this.
"""
import argparse
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from runlog import LoggingExchange, Run, to_jsonable  # noqa: E402


def connect(a):
    if a.sim:
        from optisim import SimExchange, build
        from optisim.market import Limits
        m, _ = build(a.scenario, 0, n_teams=0)
        m.add_account("us", Limits(**m.team_limits))
        e = SimExchange(m, "us")
        for _ in range(50):
            m.step()

        def wait(s):
            for _ in range(max(1, int(s / m.dt))):
                m.step()
        return e, (lambda: m.t), wait
    from optibook.synchronous_client import Exchange
    e = Exchange()
    e.connect()
    return e, time.time, time.sleep


def book_str(b, n=5):
    rows = ["  bid | price | ask"]
    levels = {}
    for pv in b.bids[:n]:
        levels.setdefault(pv.price, [0, 0])[0] += pv.volume
    for pv in b.asks[:n]:
        levels.setdefault(pv.price, [0, 0])[1] += pv.volume
    for px in sorted(levels, reverse=True):
        bv, av = levels[px]
        rows.append(f"  {bv or '':>4} | {px:>7} | {av or ''}")
    return "\n".join(rows)


def pnl_from_trades(trades, last_price):
    """Problem 7: cash from every trade + position valued at the last traded price."""
    cash, pos = 0.0, 0
    for t in trades:
        sgn = 1 if t.side == "bid" else -1
        pos += sgn * t.volume
        cash -= sgn * t.volume * t.price
    return cash + pos * (last_price or 0.0), pos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--scenario", default="bonafide_quiet")
    ap.add_argument("--instrument", help="default: the most liquid-looking stock")
    ap.add_argument("--lots", type=int, default=1)
    ap.add_argument("--hold", type=float, default=5.0, help="seconds between buying and selling back")
    ap.add_argument("--probe-rate", action="store_true")
    a = ap.parse_args()
    e, clock, wait = connect(a)
    run = Run(os.path.join(BASE, "logs"), "intro", "sim" if a.sim else "live", clock)
    x = LoggingExchange(e, run)
    out = {}

    print("== instruments")
    inst = e.get_instruments()
    get_t = getattr(e, "get_tradable_instruments", None)
    tradable = get_t() if get_t else inst
    out["instruments"] = {k: to_jsonable(v) for k, v in inst.items()}
    for k, v in inst.items():
        print(f"  {k}: tick {getattr(v, 'tick_size', '?')}, type {getattr(v, 'instrument_type', None)}, "
              f"price limit {getattr(v, 'price_change_limit', None)}, tradable {k in tradable}")
    i = a.instrument
    if i is None:
        best = None
        for k in tradable:
            b = e.get_last_price_book(k)
            if b.bids and b.asks:
                depth = b.bids[0].volume + b.asks[0].volume
                if best is None or depth > best[0]:
                    best = (depth, k)
        i = best[1] if best else sorted(tradable)[0]
    print(f"using {i}")

    print("\n== problem 6: order book")
    b = e.get_last_price_book(i)
    print(book_str(b))

    print(f"\n== problem 1: buy {a.lots} at the best ask")
    r = x.insert_order(i, price=b.asks[0].price, volume=a.lots, side="bid", order_type="ioc")
    print("  response:", to_jsonable(r))
    wait(1.0)
    print("  position:", e.get_positions().get(i))

    print(f"\n== problem 2: wait {a.hold}s, sell {a.lots} at the best bid")
    wait(a.hold)
    b = e.get_last_price_book(i)
    r = x.insert_order(i, price=b.bids[0].price, volume=a.lots, side="ask", order_type="ioc")
    print("  response:", to_jsonable(r))
    wait(1.0)
    print("  position:", e.get_positions().get(i))

    print("\n== problem 3 / 7: PnL from our trades vs get_pnl()")
    trades = e.get_trade_history(i)
    ticks = e.get_trade_tick_history(i)
    last = ticks[-1].price if ticks else None
    mine, pos = pnl_from_trades(trades, last)
    print(f"  trades: {[to_jsonable(t) for t in trades][-4:]}")
    print(f"  our calculation {mine:.4f} (position {pos}), exchange get_pnl {e.get_pnl():.4f}, cash {getattr(e, 'get_cash', lambda: None)()}")

    print("\n== problem 4: far-away order, amend, cancel (also shows the price-band error text, if any)")
    far = round(max(100000.0, b.asks[0].price * 10), 1)
    r = x.insert_order(i, price=far, volume=10, side="ask", order_type="limit")
    out["far_order_response"] = to_jsonable(r)
    print("  insert at", far, "->", to_jsonable(r))
    if not getattr(r, "success", False):
        near = round(b.asks[0].price + 20 * float(getattr(inst[i], "tick_size", 0.1)), 6)
        r = x.insert_order(i, price=near, volume=10, side="ask", order_type="limit")
        print("  retry closer at", near, "->", to_jsonable(r))
    print("  outstanding:", {k: to_jsonable(v) for k, v in e.get_outstanding_orders(i).items()})
    if getattr(r, "order_id", None) is not None:
        print("  amend to 5 ->", to_jsonable(x.amend_order(i, order_id=r.order_id, volume=5)))
        print("  outstanding:", {k: to_jsonable(v) for k, v in e.get_outstanding_orders(i).items()})
    x.delete_orders(i)
    print("  after delete_orders:", e.get_outstanding_orders(i))

    print("\n== problem 5: public trades since connecting (FAQ: no history snapshot)")
    print(f"  {len(ticks)} ticks, last 3: {[to_jsonable(t) for t in ticks[-3:]]}")

    print("\n== news feed")
    feed = getattr(e, "get_social_media_feeds_history", None)
    posts = feed() if feed else []
    out["news_sample"] = [to_jsonable(p) for p in posts[-5:]]
    print(f"  {len(posts)} posts, last: {out['news_sample'][-2:]}")

    print("\n== latency (ms per call)")
    for name in ("get_last_price_book", "get_positions", "get_outstanding_orders"):
        fn = getattr(e, name)
        t0 = time.perf_counter()
        for _ in range(20):
            fn(i) if name != "get_positions" else fn()
        print(f"  {name}: {(time.perf_counter() - t0) * 50:.2f}")
    out["order_latency_ms"] = {k: round(v[1] / v[0], 2) for k, v in x.call_stats.items() if v[0]}
    print("  order calls:", out["order_latency_ms"])

    if a.probe_rate:
        print("\n== rate limit probe: 1-lot bids 10 ticks under the best bid (cannot trade), as fast as possible")
        tk = float(getattr(inst[i], "tick_size", 0.1))
        px = round(e.get_last_price_book(i).bids[0].price - 10 * tk, 6)
        ok = rej = 0
        reasons = {}
        t0 = clock()
        for _ in range(60):
            r = x.insert_order(i, price=round(px, 6), volume=1, side="bid", order_type="limit")
            if getattr(r, "success", False):
                ok += 1
            else:
                rej += 1
                k = getattr(r, "error_reason", None) or getattr(r, "reason", None)
                reasons[k] = reasons.get(k, 0) + 1
        dt = max(1e-6, clock() - t0)
        x.delete_orders(i)
        out["rate_probe"] = {"accepted": ok, "rejected": rej, "seconds": round(dt, 3), "reasons": reasons}
        print("  ", out["rate_probe"])

    print("\n== final position check (should be 0):", e.get_positions().get(i))
    run.update_meta(intro_summary=out) if os.path.exists(os.path.join(run.dir, "meta.json")) else run.write_meta(
        {"intro_summary": out, "mode": "sim" if a.sim else "live"})
    run.close()
    print(f"\nlogged to {run.dir}")
    if not a.sim:
        e.disconnect()


if __name__ == "__main__":
    main()
