# Optiver Coding Challenge - Delft prep kit

Local Optibook-like simulator + two baseline strategies + notes from past winners.
Strategies use only the real `optibook.synchronous_client.Exchange` API, so the same file runs in the sim and live.

## Quick start

```bash
python -m pytest -q tests                                   # engine sanity (9 tests)
python run_sim.py --strategy cross_arb   --scenario basic --seeds 5
python run_sim.py --strategy quote_hedge --scenario hard  --seeds 5 -p edge=1 -p size=10
python run_sim.py --strategy quote_hedge --scenario hard  --plot equity.png
python tools/market_stats.py --scenario competitive         # spreads, cross frequency, trade counts
python tools/crowd_test.py --strategy quote_hedge -p edge=2  # PnL and rank as 0..24 rival teams join
# on the day
python tools/record_live.py --minutes 5                     # watch the real market first, no trading
python run_live.py --strategy cross_arb                     # v0 live
python run_live.py --strategy quote_hedge --pairs ASML:ASML_DUAL -p edge=1
python run_live.py --flatten                                # panic button: cancel all, close all
```

## Layout

```
optisim/      simulator: book.py (price-time matching), market.py (clock, limits, accounts, PnL),
              exchange.py (SimExchange = Optibook API), bots.py, scenarios.py
strategies/   common.py (rate budget, worst-case capacity, hedger, flatten), cross_arb.py (v0), quote_hedge.py (v1)
tools/        market_stats.py (sim calibration), record_live.py (live calibration)
run_sim.py    backtest across seeds        run_live.py   real exchange loop with crash guard + flatten on exit
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
All parameters are guesses. The sim is for testing logic and comparing variants, not predicting PnL. Recalibrate with `record_live.py` on the day.

## Baseline results (10 sim minutes, mean +- sd over seeds)

| Strategy | basic | competitive | hard |
|---|---|---|---|
| v0 cross_arb (take only) | 41 +- 35 | 4 +- 5 | 100 +- 21 |
| v1 quote_hedge (quote dual, hedge primary) | 260 +- 42 | 123 +- 10 | 292 +- 11 |

Ablations on `hard` (3 seeds): penny-jumping off 217 vs on 287; loop every 0.1s 315, 0.2s 287, 0.5s 272, 1.0s 267;
edge 1 tick best (edge 3 drops to ~160); size 10 beats 5 and 20; inventory skew had no clear benefit here.
Takeaway: once other teams exist, pure taking dies (4 in `competitive`) and passive quoting with instant hedging carries the PnL.

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
12. **Record before trading**: 5 minutes of `record_live.py` to set edge and size from real spreads.
13. **Check which listing is liquid**: in the MADLAD utils, `phil_A` points at `PHILIPS_B` and vice versa. Look at spreads and volume, don't trust names.
14. **Judging is not only PnL**: keep a PnL + delta chart and a 1-minute explanation of risk control ready.
15. Not implemented yet: microprice fair value, multiple quote levels, queue-position model, news hook.

## Day-of checklist

- [ ] `record_live.py` 5 min, note spreads, cross %, trades/min, limits and rate limit from the brief
- [ ] Tweak `scenarios.py` to match, rerun the param sweep (edge, size)
- [ ] Start live with `cross_arb` (safe), watch PnL and positions
- [ ] Switch to `quote_hedge` once hedging is confirmed working live
- [ ] Prepare the pitch: what, why it is low risk, chart, what you'd do next
