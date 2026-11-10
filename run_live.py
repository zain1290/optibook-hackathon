"""Run a strategy with full logging, against the REAL Optibook exchange or the simulator.

Live (on the day):
  python run_live.py --observe                         # trade nothing, just record the market (do this first)
  python run_live.py --strategy cross_arb
  python run_live.py --strategy quote_hedge --pairs ASML:ASML_DUAL -p edge=1
  python run_live.py --flatten                         # panic button: cancel all + close all, then exit

Same pipeline offline (tests logging, monitor and settings before Thursday):
  python run_live.py --sim crowded --teams 12 --strategy quote_hedge --minutes 10

While it runs: edit the run's settings.json (path printed at start) to change parameters live,
or set "pause": true / "flatten": true. Ctrl+C stops, cancels orders and flattens (unless --no-flatten-on-exit).
Every run writes a folder under logs/. Share it with:  python tools/pack_run.py logs/<run>
"""
import argparse
import os
import sys
import time

from run_sim import parse_params
from runlog import LoggingExchange, Recorder, Run, Settings, Tee, environment_info, to_jsonable
from strategies import STRATEGIES
from strategies.common import Ctx, flatten_all, flatten_net, hedge_net

BASE = os.path.dirname(os.path.abspath(__file__))


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


def make_session(a):
    """Returns (exchange, clock, wait, info). wait(seconds) sleeps live, advances the market in the sim."""
    if a.sim:
        from optisim import SimExchange, build
        from optisim.market import Limits
        from optisim.scenarios import TEAM_LIMITS
        m, _ = build(a.sim, a.seed, n_teams=a.teams)
        m.add_account("us", Limits(**TEAM_LIMITS))
        e = SimExchange(m, "us")

        def wait(sec):
            for _ in range(max(1, round(sec / m.dt))):
                m.step()
        return e, (lambda: m.t), wait, {"mode": "sim", "scenario": a.sim, "seed": a.seed, "teams": a.teams,
                                        "limits": TEAM_LIMITS, "dt": m.dt, "_market": m}
    from optibook.synchronous_client import Exchange  # only on the hackathon machines
    e = Exchange()
    e.connect()
    return e, time.time, time.sleep, {"mode": "live", "limits": "unknown: paste the brief into notes.md"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strategy", default="cross_arb", choices=list(STRATEGIES))
    ap.add_argument("--observe", action="store_true", help="record only, send no orders")
    ap.add_argument("--pairs", help="comma list of PRIMARY:DUAL, primary = the LIQUID listing")
    ap.add_argument("--period", type=float, default=0.15, help="seconds between loops")
    ap.add_argument("--minutes", type=float, help="stop after this long (default: until Ctrl+C; sim: 10)")
    ap.add_argument("-p", "--param", action="append", help="strategy param, e.g. -p edge=2")
    ap.add_argument("--settings", help="settings file to hot-reload (default: <run folder>/settings.json)")
    ap.add_argument("--logdir", default=os.path.join(BASE, "logs"))
    ap.add_argument("--book-depth", type=int, default=10)
    ap.add_argument("--record-every", type=int, default=1, help="record every N loops (raise if it slows the bot)")
    ap.add_argument("--metrics-every", type=float, default=10.0, help="seconds between monitor prints")
    ap.add_argument("--flatten", action="store_true", help="cancel everything, close all positions, exit")
    ap.add_argument("--no-flatten-on-exit", action="store_true", help="same as --exit none")
    ap.add_argument("--exit", choices=["all", "net", "none"], default="net",
                    help="on stop: close everything (all), only unhedged delta (net, default), or nothing")
    ap.add_argument("--sim", choices=["basic", "competitive", "hard", "crowded", "crowded_tight", "crowded_sticky", "crowded_clones"], help="run offline in the simulator")
    ap.add_argument("--teams", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.sim and a.minutes is None:
        a.minutes = 10

    e, clock, wait, sess = make_session(a)
    mode = "observe" if a.observe else ("flatten" if a.flatten else a.strategy)
    run = Run(a.logdir, mode, sess["mode"], clock)
    sys.stdout = Tee(os.path.join(run.dir, "console.log"))
    proxy = LoggingExchange(e, run)
    instruments = e.get_instruments()
    ids = sorted(instruments)
    pairs = [tuple(p.split(":")) for p in a.pairs.split(",")] if a.pairs else detect_pairs(instruments)

    strat, settings = None, None
    params = parse_params(a.param)
    if not a.observe and not a.flatten:
        if sess["mode"] == "live":
            params.setdefault("hedge_cooldown", 0.2)
        else:
            params["clock"] = clock
        strat = STRATEGIES[a.strategy](pairs, **params)
        settings = Settings(a.settings or os.path.join(run.dir, "settings.json"), strat, run)

    market = sess.pop("_market", None)
    run.write_meta({"session": sess, "strategy": None if strat is None else a.strategy,
                    "params": {k: v for k, v in params.items() if k != "clock"}, "pairs": pairs,
                    "args": {k: v for k, v in vars(a).items()}, "instruments": to_jsonable(instruments),
                    "env": environment_info(BASE), "t_start": clock(),
                    "settings_file": settings.path if settings else None,
                    "time_unit": "seconds; t = unix time live, sim seconds in --sim"})
    print(f"run folder: {run.dir}")
    print("instruments:", {k: (getattr(v, 'tick_size', None), getattr(v, 'paused', None)) for k, v in instruments.items()})
    print("pairs (primary, dual):", pairs, "<- CHECK the primary is the liquid one")
    if settings:
        print(f"live settings file: {settings.path}")
    run.event("start", mode=mode, pairs=pairs)

    if a.flatten:
        flatten_all(proxy, ids)
        print("positions after flatten:", e.get_positions())
        run.event("stop", reason="flatten only")
        run.close()
        return

    rec = Recorder(e, proxy, run, pairs, clock, depth=a.book_depth, metrics_period=a.metrics_every)
    rec.write_state(clock(), force=True)
    t_end = None if a.minutes is None else clock() + a.minutes * 60
    if strat is not None and t_end is not None and hasattr(strat, "end_time"):
        strat.end_time = t_end  # lets the strategy wind down inventory before the end
    n, was_paused, reason = 0, False, "time limit"
    pause_ctx = None
    try:
        while t_end is None or clock() < t_end:
            t0 = time.perf_counter()
            if strat is not None:
                settings.poll()
                fl = settings.flags
                try:
                    if fl.get("flatten"):
                        run.event("manual_flatten")
                        flatten_all(proxy, ids)
                        fl["flatten"] = False
                        print("flattened. set \"flatten\" back to false in settings.json")
                    if fl.get("pause"):
                        if not was_paused:
                            for i in ids:
                                proxy.delete_orders(i)
                            run.event("paused_by_settings")
                            pause_ctx = pause_ctx or Ctx(proxy, getattr(strat, "limit", 100), strat.budget)
                        if fl.get("hedge_when_paused", True):
                            pos = e.get_positions()
                            for P, D in pairs:
                                hedge_net(pause_ctx, P, D, pos)
                    else:
                        if was_paused:
                            run.event("resumed_by_settings")
                        strat.step(proxy)
                    was_paused = bool(fl.get("pause"))
                except Exception as ex:  # one bad response must never kill the bot
                    run.error("strategy.step", ex)
                    print("step error:", repr(ex))
            loop_ms = (time.perf_counter() - t0) * 1000
            n += 1
            if n % a.record_every == 0:
                try:
                    rec.snapshot(loop_ms)
                except Exception as ex:
                    run.error("recorder", ex)
            if sess["mode"] == "live":
                wait(max(0.0, a.period - (time.perf_counter() - t0)))
            else:
                wait(a.period)
    except KeyboardInterrupt:
        reason = "ctrl+c"
        print("stopping")
    finally:
        try:
            exit_mode = "none" if a.no_flatten_on_exit else a.exit
            if strat is not None and exit_mode == "all":
                flatten_all(proxy, ids)
            elif strat is not None and exit_mode == "net":
                flatten_net(proxy, pairs)
            elif strat is not None:
                for i in ids:
                    proxy.delete_orders(i)
            if sess["mode"] == "sim":
                wait(0.5)
            rec.snapshot()
            final = rec.write_state(clock(), force=True)
            rec.emit_metrics(clock())
        except Exception as ex:
            run.error("shutdown", ex)
            final = {}
        if market is not None:  # sim only: the true leaderboard (on the day, read it off the screen)
            board = sorted(({"name": k, "pnl": round(market.pnl(k), 2), "volume": acc.volume_traded,
                             "max_abs_net_delta": acc.max_abs_delta}
                            for k, acc in market.accounts.items() if k == "us" or k.startswith("team")),
                           key=lambda r: -r["pnl"])
            rank = 1 + next(i for i, r in enumerate(board) if r["name"] == "us")
            run.update_meta(leaderboard=board, rank=rank, n_competitors=len(board))
            print(f"rank {rank}/{len(board)} | top: " + ", ".join(f"{r['name']} {r['pnl']}" for r in board[:3]))
        run.event("stop", reason=reason, loops=n)
        run.update_meta(t_end=clock(), stop_reason=reason, loops=n, final=final,
                        rows={s: w.n for s, w in run.w.items()}, errors=run.counters["errors"])
        run.close()
        print(f"final: {final}")
        print(f"logs: {run.dir}\nshare: python tools/pack_run.py \"{run.dir}\"")


if __name__ == "__main__":
    main()
