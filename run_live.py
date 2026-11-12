"""Run a strategy with full logging, against the REAL Optibook exchange or the simulator.

Live (on the day):
  python run_live.py --observe                         # trade nothing, just record the market (do this first)
  python run_live.py --strategy combo                  # stocks + any derivatives, one connection
  python run_live.py --strategy stock_mm -p size=10    # stocks only
  python run_live.py --strategy evolved --pairs ASML:ASML_DUAL   # if the brief turns out to be a dual listing
  python run_live.py --flatten                         # panic button: cancel all + close all, then exit

ONE CONNECTION PER TEAM: a second program (or a teammate's notebook) connecting with the team login kicks
this one off, and the exchange then cancels all its orders. This runner reconnects by itself, but only run
one program per team. Teammates watch the web visualizer instead.

Same pipeline offline (tests logging, monitor and settings before Thursday):
  python run_live.py --sim bonafide --teams 12 --strategy combo --minutes 10

While it runs: edit the run's settings.json (path printed at start) to change parameters live,
or set "pause": true / "flatten": true. Ctrl+C stops, cancels orders and flattens (unless --no-flatten-on-exit).
Every run writes a folder under logs/. Share it with:  python tools/pack_run.py logs/<run>
"""
import argparse
import os
import sys
import time

from optisim.scenarios import SCENARIOS
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


LOCK = os.path.join(BASE, "logs", "LIVE_CONNECTION.lock")


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def take_live_lock(force=False):
    """Only one program per team may hold the exchange connection. Refuse to start a second one."""
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    if os.path.exists(LOCK) and not force:
        try:
            pid = int(open(LOCK).read().split()[0])
        except Exception:
            pid = -1
        if pid > 0 and _pid_alive(pid) and pid != os.getpid():
            raise SystemExit(f"Another live program (pid {pid}) already holds the team's exchange connection.\n"
                             "Starting a second one would kick it off and cancel all its orders.\n"
                             "Stop it first, or pass --force if you are sure it is dead.")
    with open(LOCK, "w") as f:
        f.write(f"{os.getpid()} {time.time()}")


def release_live_lock():
    try:
        if os.path.exists(LOCK) and open(LOCK).read().split()[0] == str(os.getpid()):
            os.remove(LOCK)
    except Exception:
        pass


def ensure_connected(e, run, state):
    """Reconnect if another connection kicked us off or the link dropped. Returns True when connected.
    After a drop the exchange has cancelled our orders (Cancel On Disconnect); strategies rebuild their
    quotes from get_outstanding_orders / get_positions on the next loop, so nothing else is needed."""
    check = getattr(e, "is_connected", None)
    try:
        ok = check() if callable(check) else True
    except Exception:
        ok = False
    if ok:
        return True
    now = time.time()
    if now - state.get("last_try", 0) < state.get("backoff", 0.5):
        return False
    state["last_try"] = now
    state["drops"] = state.get("drops", 0) + 1
    run.event("disconnected", drops=state["drops"])
    print(f"connection lost (#{state['drops']}): orders were cancelled by the exchange; reconnecting")
    try:
        e.connect()
        state["backoff"] = 0.5
        run.event("reconnected", drops=state["drops"])
        print("reconnected")
        return True
    except Exception as ex:
        state["backoff"] = min(10.0, state.get("backoff", 0.5) * 2)
        run.error("reconnect", ex)
        return False


def make_session(a):
    """Returns (exchange, clock, wait, info). wait(seconds) sleeps live, advances the market in the sim."""
    if a.sim:
        from optisim import SimExchange, build
        from optisim.market import Limits
        m, _ = build(a.sim, a.seed, n_teams=a.teams)
        TEAM_LIMITS = m.team_limits
        m.add_account("us", Limits(**TEAM_LIMITS))
        e = SimExchange(m, "us")
        wall0 = time.time()

        def wait(sec):
            for _ in range(max(1, round(sec / m.dt))):
                m.step()
            if a.speed > 0:  # rehearsal: keep the simulated clock in step with the wall clock
                ahead = m.t / a.speed - (time.time() - wall0)
                if ahead > 0:
                    time.sleep(ahead)
        return e, (lambda: m.t), wait, {"mode": "sim", "scenario": a.sim, "seed": a.seed, "teams": a.teams,
                                        "limits": TEAM_LIMITS, "dt": m.dt, "_market": m}
    from optibook.synchronous_client import Exchange  # only on the hackathon machines
    e = Exchange()
    e.connect()
    return e, time.time, time.sleep, {"mode": "live", "limits": "unknown: paste the brief into notes.md"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strategy", default="combo", choices=list(STRATEGIES))
    ap.add_argument("--observe", action="store_true", help="record only, send no orders")
    ap.add_argument("--pairs", help="comma list of PRIMARY:DUAL, primary = the LIQUID listing")
    ap.add_argument("--period", type=float, default=0.1, help="seconds between loops (faster wins pick-offs)")
    ap.add_argument("--minutes", type=float, help="stop after this long (default: until Ctrl+C; sim: 10)")
    ap.add_argument("-p", "--param", action="append", help="strategy param, e.g. -p edge=2")
    ap.add_argument("--settings", help="settings file to hot-reload (default: <run folder>/settings.json)")
    ap.add_argument("--logdir", default=os.path.join(BASE, "logs"))
    ap.add_argument("--book-depth", type=int, default=10)
    ap.add_argument("--record-every", type=int, default=1, help="record every N loops (raise if it slows the bot)")
    ap.add_argument("--poll-every", type=int, default=3,
                    help="recorder fetches new trades every N recorded loops (no data lost; fewer exchange calls)")
    ap.add_argument("--metrics-every", type=float, default=10.0, help="seconds between monitor prints")
    ap.add_argument("--flatten", action="store_true", help="cancel everything, close all positions, exit")
    ap.add_argument("--no-flatten-on-exit", action="store_true", help="same as --exit none")
    ap.add_argument("--exit", choices=["all", "net", "none"], default="net",
                    help="on stop: close everything (all), only unhedged delta (net, default), or nothing")
    ap.add_argument("--sim", choices=list(SCENARIOS), help="run offline in the simulator")
    ap.add_argument("--teams", type=int, default=12)
    ap.add_argument("--force", action="store_true", help="live: start even if the connection lock is held")
    ap.add_argument("--kick-after", type=float, default=None,
                    help="sim only: simulate a teammate connecting after N seconds (tests reconnect)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--speed", type=float, default=0.0,
                    help="sim only: 1 = real time (rehearsal), 5 = 5x faster, 0 = as fast as possible")
    a = ap.parse_args()
    if a.sim and a.minutes is None:
        a.minutes = 10

    if not a.sim:
        take_live_lock(a.force)
    e, clock, wait, sess = make_session(a)
    if sess["mode"] == "live":  # pace every close-out: >25 requests/s gets the connection cut (measured 12 Nov)
        import strategies.common as _common
        _common.FLATTEN_PACE = 0.08
    mode = "observe" if a.observe else ("flatten" if a.flatten else a.strategy)
    run = Run(a.logdir, mode, sess["mode"], clock)
    sys.stdout = Tee(os.path.join(run.dir, "console.log"))
    proxy = LoggingExchange(e, run)
    instruments = e.get_instruments()
    ids = sorted(instruments)
    try:
        tradable = sorted(getattr(e, "get_tradable_instruments", e.get_instruments)())
    except Exception:
        tradable = ids
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
    if pairs:
        print("pairs (primary, dual):", pairs, "<- CHECK the primary is the liquid one")
    print(f"tradable now: {tradable}")
    if strat is not None and a.strategy in ("evolved", "quote_hedge", "cross_arb") and not pairs:
        print("WARNING: this strategy trades dual listings but no pairs were found. Use --strategy combo / stock_mm.")
    if settings:
        print(f"live settings file: {settings.path}")
    run.event("start", mode=mode, pairs=pairs)

    if a.flatten:
        flatten_all(proxy, ids)
        print("positions after flatten:", e.get_positions())
        run.event("stop", reason="flatten only")
        run.close()
        return

    rec = Recorder(e, proxy, run, pairs, clock, depth=a.book_depth, metrics_period=a.metrics_every,
                   poll_every=a.poll_every)
    rec.write_state(clock(), force=True)
    t_end = None if a.minutes is None else clock() + a.minutes * 60
    if strat is not None and t_end is not None and hasattr(strat, "end_time"):
        strat.end_time = t_end  # lets the strategy wind down inventory before the end
    n, was_paused, reason = 0, False, "time limit"
    pause_ctx = None
    conn = {}
    kick_at = None if a.kick_after is None or market is None else clock() + a.kick_after
    try:
        stop_file = os.path.join(run.dir, "STOP")  # created by the control panel (or by hand) to stop cleanly
        while t_end is None or clock() < t_end:
            t0 = time.perf_counter()
            proxy.begin_loop()  # fresh reads this loop; within it the bot and the recorder share them
            if os.path.exists(stop_file):
                reason = "stop requested"
                print("stop requested")
                break
            if kick_at is not None and clock() >= kick_at:  # sim: a teammate's notebook logs in
                from optisim import SimExchange
                SimExchange(market, "us")
                kick_at = None
                print("sim: another connection logged in with our account (we get kicked)")
            if not ensure_connected(e, run, conn):
                wait(0.5 if sess["mode"] == "live" else a.period)
                continue
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
                    if isinstance(ex, ConnectionError):
                        ensure_connected(e, run, conn)
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
            if sess["mode"] == "live":
                wait(1.0)  # let the last second's order budget drain before closing out
            exit_mode = "none" if a.no_flatten_on_exit else a.exit
            others = [i for i in tradable if not any(i in p for p in pairs)]
            for attempt in range(8):  # retry: closing orders can be rate-limited or only partly filled
                if strat is not None and exit_mode == "all":
                    flatten_all(proxy, ids)
                elif strat is not None and exit_mode == "net":
                    flatten_net(proxy, pairs, others=others)
                elif strat is not None:
                    for i in ids:
                        proxy.delete_orders(i)
                wait(0.5 if sess["mode"] == "sim" else 0.4)
                pos = e.get_positions()
                left = {i: v for i, v in pos.items() if v and (exit_mode == "all" or i in others)}
                if strat is None or exit_mode == "none" or not left:
                    break
                print(f"still open after close attempt {attempt + 1}: {left}")
            proxy.begin_loop()
            rec.snapshot(force_poll=True)  # always collect the closing fills
            final = rec.write_state(clock(), force=True)
            rec.emit_metrics(clock())
        except Exception as ex:
            run.error("shutdown", ex)
            final = {}
        if market is not None:  # sim only: the true leaderboard (on the day, read it off the screen)
            from optisim.market import hourly_sharpe
            board = sorted(({"name": k, "pnl": round(market.pnl(k), 2), "pnl_last": round(market.pnl(k, "last"), 2),
                             "hourly_sharpe": hourly_sharpe(acc.equity_curve), "volume": acc.volume_traded,
                             "max_abs_net_delta": acc.max_abs_delta}
                            for k, acc in market.accounts.items() if k == "us" or k.startswith("team")),
                           key=lambda r: -r["pnl"])
            rank = 1 + next(i for i, r in enumerate(board) if r["name"] == "us")
            run.update_meta(leaderboard=board, rank=rank, n_competitors=len(board))
            print(f"rank {rank}/{len(board)} | top: " + ", ".join(f"{r['name']} {r['pnl']}" for r in board[:3]))
        run.event("stop", reason=reason, loops=n)
        if sess["mode"] == "live":
            release_live_lock()
        run.update_meta(t_end=clock(), stop_reason=reason, loops=n, final=final, reconnects=conn.get("drops", 0),
                        rows={s: w.n for s, w in run.w.items()}, errors=run.counters["errors"])
        run.close()
        print(f"final: {final}")
        print(f"logs: {run.dir}\nshare: python tools/pack_run.py \"{run.dir}\"")


if __name__ == "__main__":
    main()
