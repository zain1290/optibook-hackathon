# Optiver Coding Challenge - Delft prep kit

Local Optibook-like simulator + strategies + logging + a control panel with a plain-language Handbook.
Strategies use only the real `optibook.synchronous_client.Exchange` API, so the same file runs in the sim and live.

## The Bona Fide setup (from the practice exchange, 11 Nov)

The practice exchange is **eight stocks** (AMD, AVGO, NVDA, MU, SNDK, CRWV, NBIS, VRT), one big exchange maker per
book, 20-lot background traders, a news feed, and **one connection per team** (a second one kicks the first and
the exchange cancels its orders). Details: `docs/bona_fide_site_findings.md`. Getting the code into Optiver's
browser VS Code: `docs/DEPLOY.md`.

- **Run on the day:** `python run_live.py --strategy combo` (stocks + any options/futures/ETFs, one connection).
  It reconnects by itself if kicked, refuses to start a second live program, and closes positions on stop.
- **Simulator:** `--sim bonafide` (with rivals), `bonafide_quiet` (as seen), `bonafide_clones`, `bonafide_informed`,
  `bonafide_leadlag`, `bonafide_derivs`. Rehearse a kick: `--kick-after 60`.
- **First checks on the real exchange:** `python tools/intro_exercises.py [--probe-rate]` (1-lot orders).
- **After observing:** `tools/news_impact.py` (does news move prices?), `tools/pair_stats.py` (pairs worth trading?).

| strategy | what it does | sim result (10 min, 6 markets, 12 rivals) |
|---|---|---|
| `combo` | stock_mm + deriv_arb (+ optional pairs), shared order budget | bonafide_derivs: +9,200 (deriv maker is easy, treat as a check) |
| `stock_mm` | quote 1 tick inside the exchange maker, pick off stale/dumped quotes, step aside on news | bonafide: +1,962, 1st in 3/6; without picking off about 0 |
| `deriv_arb` | Black-Scholes / futures / ETF fair values, take mispricings, delta-hedge | standby; does nothing if no derivatives |
| `pairs` | z-score of log price gap between sector pairs | -92 alone (spreads cost more than the gaps): off by default |
| `evolved` v0-v10 | dual-listing quote + hedge | only if the brief is a dual listing |

## Control panel (no command line needed)

```bash
python ui/server.py          # opens http://127.0.0.1:8050 in your browser
```

One page for everything: **Run** (observe the live market, trade live, rehearse on the simulator in real time, flatten now;
pick strategy, version and every parameter), **Monitor** (PnL, positions, prices with our fills, quotes vs rivals,
where the money comes from, health, events, console, notes), **live settings** (change size, min_profit or any strategy
flag while the bot runs, pause/resume, flatten), **Past runs** (report, chart, download zip) and **Backtest** (compare
versions or tweaks on held-out markets). The status bar is blue for observe/rehearsal and red-striped for live trading;
Stop and Flatten are always in it. Live and flatten modes ask for a second click. Standard library only, works offline.
`--host 0.0.0.0` makes it reachable from another machine (e.g. a hackathon VM); `--port` changes the port.

**New to trading? Open the Handbook tab first.** It explains the market, the dual-listing challenge, how the bot
makes money, every button and every setting in plain words, with no background assumed: what each setting does,
its unit, and when to change it. It also has a day plan, an "if you see this, do that" table, troubleshooting and a
glossary of every term. Every `?` next to a setting or column opens the matching explanation, and the search box
finds any term. The Run tab walks you through three steps (what to do, which strategy, settings), with quick-start
presets and a plain-English summary of what Start will do. The Monitor has a "What to do now" card that turns the
numbers into advice. Sources: `ui/handbook.md` (text) and `ui/params.json` (one entry per setting).

## Quick start

```bash
python -m pytest -q tests                                   # engine, logging, panel, Bona Fide tests (22)
python tools/bench.py combo stock_mm stock_mm:take_edge=0 --scenario bonafide   # compare strategies/settings
python run_live.py --sim bonafide --strategy combo --minutes 10 --speed 5       # rehearse the live pipeline
python run_sim.py --strategy cross_arb   --scenario basic --seeds 5
python run_sim.py --strategy quote_hedge --scenario hard  --seeds 5 -p edge=1 -p size=10
python run_sim.py --strategy quote_hedge --scenario hard  --plot equity.png
python tools/market_stats.py --scenario competitive         # spreads, cross frequency, trade counts
python tools/crowd_test.py --strategy quote_hedge -p edge=2  # PnL and rank as 0..24 rival teams join
# on the day
python run_live.py --observe --minutes 5                    # watch the real market first, no trading
python run_live.py --strategy cross_arb                     # v0 live
python run_live.py --strategy quote_hedge --pairs ASML:ASML_DUAL -p edge=1
python run_live.py --strategy evolved --period 0.1           # latest version (v10); -p version=v8 for size 10
python run_live.py --flatten                                # panic button: cancel all, close all
python tools/pack_run.py logs/<run>                         # report + chart + zip to share
# rehearse the exact live pipeline offline
python run_live.py --sim crowded --teams 12 --strategy quote_hedge --minutes 10
```

## Layout

```
optisim/      simulator: book.py (price-time matching), market.py (clock, limits, accounts, PnL),
              exchange.py (SimExchange = Optibook API), bots.py, scenarios.py
strategies/   common.py (rate budget with urgent reserve, capacity, hedger, flatten), stock_mm.py, deriv_arb.py,
              pricing.py (Black-Scholes, Greeks, futures, ETF), news.py (post reader), pairs.py, combo.py,
              cross_arb.py, quote_hedge.py, evolved.py (dual listing)
runlog/       logging: core.py (run folder, exchange proxy), recorder.py (market snapshots + live monitor), settings.py (hot reload)
tools/        analyze_run.py (report + chart), pack_run.py (zip to share), bench.py, intro_exercises.py,
              news_impact.py, pair_stats.py, make_bundle.py (zip / paste-installer for the Dev Environment), ...
run_sim.py    fast backtest across seeds   run_live.py   live or --sim loop with full logging, monitor, hot settings, flatten on exit
```

## What the simulator models

| Thing | How |
|---|---|
| Instruments | Each stock has a liquid primary (`ASML`) and an illiquid dual listing (`ASML_DUAL`), tick 0.1 |
| Fair value | Random walk per stock + optional news jumps |
| Exchange bots | Primary MM (knows fair value, tight, deep, requotes every step). Dual MM (slow, wide, small, quotes a stale + noisy fair value: this creates the opportunities). Random customer flow on both. Informed taker that picks off stale quotes on the dual (adverse selection) |
| Other teams | `team_arb` (CrossArb, slower loop) and `team_maker` (QuoteHedge, wider, slower), running through their own SimExchange with the same limits as us |
| Rules | Position limit 100 per instrument (worst case incl. resting orders), 25 ops/s, self-trade prevention, off-tick rejection, IOC vs limit, amend down keeps queue priority, amend up loses it, pauses (primary closed for a minute in `hard`) |
| Latency | Actor order is shuffled every 0.1s step, our loop runs every N steps (`--every`) |
| Scoring | PnL marked at true fair value (honest) and at book mid (what a dashboard shows), drawdown, max net delta, ops, rejects. Zero-sum check across all accounts every run |

Scenarios: `basic` (1 stock, no teams), `competitive` (+2 teams, informed flow, rare jumps), `hard` (2 stocks, frequent jumps, teams, informed flow, primary paused 300-360s), `crowded` (competitive market + N AI-style teams, see below).
All parameters are guesses. The sim is for testing logic and comparing variants, not predicting PnL. Recalibrate on the day from `run_live.py --observe` + `tools/analyze_run.py` (it prints a calibration block).

## Baseline results (10 sim minutes, mean +- sd over seeds)

| Strategy | basic | competitive | hard |
|---|---|---|---|
| v0 cross_arb (take only) | 41 +- 35 | 4 +- 5 | 100 +- 21 |
| v1 quote_hedge (quote dual, hedge primary) | 260 +- 42 | 123 +- 10 | 292 +- 11 |

Ablations on `hard` (3 seeds): penny-jumping off 217 vs on 287; loop every 0.1s 315, 0.2s 287, 0.5s 272, 1.0s 267;
edge 1 tick best (edge 3 drops to ~160); size 10 beats 5 and 20; inventory skew had no clear benefit here.
Takeaway: once other teams exist, pure taking dies (4 in `competitive`) and passive quoting with instant hedging carries the PnL.

## 10 rounds of improvement: `strategies/evolved.py` (v0 -> v10)

`quote_hedge.py` is the frozen original. `evolved.py` holds every version as feature flags (`-p version=v6` reruns any of them).
Each round: play a logged 10-minute round (`tools/round.py`), read `report.md`, change one thing, benchmark it on 8 held-out
markets and on robustness markets (`tools/bench.py`), adopt or reject. Full walkthrough: `notebooks/strategy_evolution.ipynb`.

| version | change (from the logs) | standard market PnL / rank |
|---|---|---|
| v0 | original | -4.3 / 7.25 |
| v1 | rest the hedge inside the primary spread instead of crossing it | 6.1 / 5.25 |
| v2 | sticky quotes, quote first, single-leg arb (fixes churn and a self-trade) | 10.7 / 4.12 |
| v3 | quote at fair +- (measured hedge cost + min profit); stop reading own hedge as market | 47.3 / 1.62 |
| v4 | inventory skew only near the position limit (position is hedged anyway) | 58.3 / 1.38 |
| v6 | adaptive hedge ladder: touch -> mid -> IOC, touch step only where it fills | 87.6 / 1.25 |
| v8 | arb unwind threshold depends on hedge cost (fixes the 1-tick market: -34.7 -> +3.2) | 87.5 / 1.12 |
| v10 | quote size 15 (marginal; worse on a 1-tick market, raise live via settings) | 90.2 / 1.25 |

v5 (artifact of the sim's market maker), v7 wind-down and v9 queue-jumping were tested and rejected; v9 adopted a faster loop.
Round results: 1st in 8 of 10 rounds (2nd vs clones of ourselves in round 10, 3rd behind two unhedged gamblers in round 4,
10th in round 2 before the churn fix). Among risk-controlled rivals, v8/v10 rank 1st in every standard and sticky benchmark market.

```bash
python tools/round.py 11 --version v10                        # play another logged round
python tools/bench.py v8 v10 --scenario crowded_tight --exit net
python tools/eval_versions.py && python tools/build_notebook.py --execute
```

## Crowded market: what happens when everyone ships the same AI-written bot

`--scenario crowded --teams N` adds N competitors: ~60% quote+hedge variants, ~30% cross-arb, ~10% buggy
(quotes, never hedges, panic-dumps at the limit). Random parameters and loop speeds. `python tools/crowd_test.py`.

| Teams | v1 quote_hedge PnL | Our rank | v0 cross_arb PnL |
|---|---|---|---|
| 0 | 228 | 1/1 | 20 |
| 3 | 50 | 1/4 | 5 |
| 6 | 26 | 2.3/7 | 6 |
| 12 | -5 | 7.7/13 | 0 |
| 24 | -4 | 9.3/25 | 1 |

Money flow (2 seeds avg): with 0 teams, all teams together make ~210; with 12 teams, ~16 split 13 ways.
The dual's spread gets competed away, customers on the dual pay less, the edge goes to zero.
The exchange's primary market maker keeps earning ~2,300-2,800 from primary flow in both cases (nobody competes for it in this sim).

Variants at 12 teams: edge 0 is worst (-14, rank 11/13), wider edge only loses less (-3), a faster loop (0.1s) with edge 2 is the only one in the black (+6, rank 4/13).
Lesson: in a crowd the copied strategy is worth ~0. The edge comes from (a) speed and clean execution on the shared idea,
(b) finding a pool of flow the crowd is not fighting over, (c) collecting from other teams' bugs. All three are only visible live.

## What past winners did, why, and does it apply to us

| Source | Setup they faced | What they did | Why it worked | Use for Delft? |
|---|---|---|---|---|
| MADLAD, Hex Cambridge 2021. Also circulated as the "example solution" in an ETH 2023 attendee's materials | PHILIPS_A/B dual listing, limit 200 | Quote the illiquid listing outside the liquid book (+ "pillow"), hedge every fill on the liquid one with IOC, tighten every 9 loops, widen after fills, unwind when free | Wide illiquid book + customer flow = spread capture with near-zero delta | Yes, this is v1. We fixed: delete+reinsert every update (burns rate limit, loses queue), positions ignore resting orders, blocking sleep |
| pcheras repo, dual-listing script | Same | Pure IOC cross arb both legs | Free money when the dual is crossed | Yes, v0. Dies once other teams compete for crosses |
| hackaTUM 2025, 3rd PnL | 5 stocks each dual-listed, news feed, 25 ops/s | MM with microprice + imbalance, stat arb primary vs dual, LLM news classifier for direction | Their stated edge: modelling queue priority and choosing amend vs cancel vs insert under the rate limit | Yes if Delft has a rate limit (likely). News part only if there is a news feed |
| hackaTUM 2024 | ETF EU/US + 3 stocks, limit 750 | MM + basket arb + dual-listing arb + central rate limiter; separate logic when one market is closed | Multiple uncorrelated edges, one shared rate budget | Rate limiter and paused-market handling: yes |
| ICHack 2025 Optiver | Dual-market phase, then single-market phase | Dual-listing arb when both open, z-score stat arb when one closed | Did not stop earning when the hedge venue closed | Yes: plan what you do when the primary pauses |
| IC Hack 2025 winners (LinkedIn) | Optibook MM challenge | Price model + always the tightest two-sided quote | Queue priority + flow capture | Yes, supports v1 |
| UNSW 2026 coursework, ASML/ASML_DUAL (closest format to ours) | ~5 competing participants | Interpolated position targets by spread, crossed arb, MM around common fair, spill hedger | Real lesson list: count resting orders in position limits, cancel stale quotes before active orders (self-trade), one sign bug froze a direction for most of a run, rivals queue ahead | Yes, all of it is built in |
| LSE winner | Several stocks, historical data given | Cointegration pairs trading | Mean reversion with pre-fitted ratios | Only if they give historical data |
| HackTheBurgh winners | News-driven | Sentiment model on headlines | Direction on news | Only if there is a news feed |

## Small tricks, big results (all implemented unless marked)

1. **Worst-case position check**: position + all resting orders on that side must stay inside the limit. Otherwise you get rejects and one side freezes.
2. **Trade the scarce leg first**: hit the dual (it vanishes), then the primary. Hedge what actually filled.
3. **Stateless hedger**: every loop, flatten `pos_primary + pos_dual` on the primary. Partial fills and missed legs self-heal. Live: 0.2s cooldown so slow position updates don't cause a double hedge.
4. **Unwinding needs less edge than opening**: trades that reduce dual inventory are allowed at 0 edge, so you never sit at +100 with one side dead.
5. **Penny, but capped**: quote 1 tick better than the best OTHER quote, never past primary +- edge. Worth ~30% in the sim.
6. **Don't touch unchanged quotes**: no cancel/replace if the price is the same, amend down to shrink. Saves ops and keeps queue priority.
7. **Remove your own orders from the book** before computing where others are.
8. **Client-side rate budget below the limit** (20 vs 25), so the hedge is never the order that gets rejected.
9. **Loop speed matters**: no prints in the hot loop, logger level ERROR, short sleep.
10. **Pull dual quotes if the primary is paused** (fills could not be hedged). Emergency hedge on the dual only if delta gets big.
11. **Crash-proof loop + kill switch**: try/except around each step, `--flatten` ready, cancel stale orders on start.
12. **Record before trading**: 5 minutes of `run_live.py --observe` to set edge and size from real spreads.
13. **Check which listing is liquid**: in the MADLAD utils, `phil_A` points at `PHILIPS_B` and vice versa. Look at spreads and volume, don't trust names.
14. **Judging is not only PnL**: keep a PnL + delta chart and a 1-minute explanation of risk control ready.
15. Not implemented yet: microprice fair value, multiple quote levels, queue-position model, news hook.

## Logging: every run is fully recorded

Every `run_live.py` run (live, `--observe` or `--sim`) writes `logs/<time>_<strategy>_<mode>/`:

| File | What | Why it matters |
|---|---|---|
| meta.json | mode, strategy, params, pairs, full instrument reference data, code version, final state | what was running |
| book.jsonl | every instrument's order book (10 levels) whenever it changes | rebuild the market, spreads, crosses, mids for markouts |
| ticks.jsonl | every public trade, all fields incl. buyer/seller names if the client gives them | who trades, how much, who is aggressive |
| orders.jsonl | every insert/amend/delete we send: request, full response, reject reason, latency, tag | rejects, rate use, why each order was sent |
| fills.jsonl | every fill: tag, order type, fair mid at fill, edge in ticks | what makes and loses money |
| own_orders.jsonl | our resting orders whenever they change | queue/competition at our price |
| state.jsonl | positions, PnL, net delta per pair (1 s and on change) | risk over time |
| instruments.jsonl | instrument data whenever it changes | pauses, new products |
| metrics.jsonl | the monitor every 10 s (also printed): spreads, crossed %, others at/better than our quotes, fills and edge by tag, markouts 1/5/30 s, ops/s, rejects, throttles, latency, loop time | live tuning |
| events.jsonl | quote target changes with inputs, arbs, hedges, settings changes, pauses, errors with traceback | why the bot did what it did |
| console.log, notes.md | terminal output; your notes (paste the brief, leaderboard, what you changed) | context the bot can't see |
| settings.json | live parameters: edit while running, applies in ~1 s; `"pause": true`, `"flatten": true` | change strategy without restarting |

After a run: `python tools/analyze_run.py logs/<run>` writes `report.md` + `overview.png` (PnL, positions, mids with our fills):
market stats, counterparties, our order mix, rejects, latency, peak ops/s, PnL attribution by tag with markouts, risk, errors,
and a sim calibration line. `python tools/pack_run.py logs/<run>` (or `--all`) zips it to share.
If the bot slows down live, raise `--record-every` (the monitor prints recorder vs strategy loop time).

## Day-of checklist

- [ ] `run_live.py --observe` 5 min, then `analyze_run.py`; paste the brief (limits, rate limit, scoring) into notes.md
- [ ] Tweak `scenarios.py` to match, rerun the param sweep (edge, size)
- [ ] Start live with `cross_arb` (safe), watch PnL and positions
- [ ] Switch to `evolved` (v8 if the primary spread is 1 tick, v10 if >= 2) once hedging is confirmed working live
- [ ] Check the brief: may we finish holding a hedged pair? If not, use `--exit all`
- [ ] Prepare the pitch: what, why it is low risk, chart, what you'd do next
