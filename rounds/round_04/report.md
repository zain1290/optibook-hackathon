# Run report: 20261111-000423_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 104)
- Strategy: **evolved**, params {'version': 'v3'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **31.10**, max drawdown 6.20, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **3/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | team01_buggy | 61.69 | 98 | 84 |
| 2 | team02_buggy | 33.75 | 64 | 64 |
| 3 | us | 31.10 | 788 | 30 |
| 4 | team04_buggy | 19.34 | 42 | 42 |
| 5 | team03_quote_hedge | 5.50 | 290 | 8 |
| 6 | team07_quote_hedge | 3.80 | 150 | 7 |
| 7 | team11_quote_hedge | 1.70 | 172 | 7 |
| 8 | team06_quote_hedge | -1.00 | 156 | 5 |
| 9 | team10_quote_hedge | -1.40 | 206 | 5 |
| 10 | team08_quote_hedge | -2.70 | 162 | 10 |
| 11 | team00_quote_hedge | -9.10 | 738 | 10 |
| 12 | team05_quote_hedge | -15.30 | 1094 | 10 |
| 13 | team09_quote_hedge | -23.50 | 1252 | 20 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.95 | 37.63 | 99.98 | 284.36 | 2082.36 | 0.41 |
| ASML_DUAL | 0.10 | 1.84 | 53.32 | 99.98 | 59.75 | 271.37 | 0.25 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.00 | - |

### Counterparties (17 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 20580 | 83 | 49.37 |
| ASML | flow_ASML | 18606 | 18606 | 44.64 |
| ASML_DUAL | flow_ASML_DUAL | 2135 | 2135 | 39.30 |
| ASML_DUAL | team09_quote_hedge | 632 | 0 | 11.63 |
| ASML | team09_quote_hedge | 620 | 620 | 1.49 |
| ASML_DUAL | mm_ASML_DUAL | 581 | 250 | 10.70 |
| ASML_DUAL | team05_quote_hedge | 549 | 15 | 10.11 |
| ASML | team05_quote_hedge | 545 | 545 | 1.31 |
| ASML_DUAL | us | 394 | 80 | 7.25 |
| ASML | us | 394 | 50 | 0.95 |
| ASML | team00_quote_hedge | 369 | 369 | 0.89 |
| ASML_DUAL | team00_quote_hedge | 369 | 10 | 6.79 |
| ASML_DUAL | team03_quote_hedge | 145 | 69 | 2.67 |
| ASML | team03_quote_hedge | 145 | 145 | 0.35 |
| ASML_DUAL | team10_quote_hedge | 103 | 20 | 1.90 |
| ASML | team10_quote_hedge | 103 | 103 | 0.25 |
| ASML_DUAL | team01_buggy | 98 | 45 | 1.80 |
| ASML | team11_quote_hedge | 86 | 86 | 0.21 |
| ASML_DUAL | team11_quote_hedge | 86 | 41 | 1.58 |
| ASML_DUAL | team08_quote_hedge | 81 | 0 | 1.49 |
| ASML | team08_quote_hedge | 81 | 81 | 0.19 |
| ASML_DUAL | team06_quote_hedge | 78 | 8 | 1.44 |
| ASML | team06_quote_hedge | 78 | 78 | 0.19 |
| ASML | team07_quote_hedge | 75 | 75 | 0.18 |
| ASML_DUAL | team07_quote_hedge | 75 | 7 | 1.38 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 490 | 48.96 |
| delete_order | requote | 478 | 47.76 |
| insert_order | hedge_passive | 103 | 10.29 |
| delete_order | hedge_cancel | 22 | 2.20 |
| insert_order | arb_dual | 4 | 0.40 |
| insert_order | hedge | 3 | 0.30 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.04 |
| delete_order | 0.00 | 0.00 | 0.02 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **15**, average 1.84/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| hedge_passive | 103 | 344 | -0.11 | -0.32 | -0.54 | -0.17 | -3.75 |
| quote | 84 | 314 | 0.64 | 1.08 | 1.36 | 0.90 | 20.10 |
| arb_dual | 6 | 70 | 1.04 | 1.59 | 2.27 | 2.40 | 7.30 |
| hedge | 3 | 40 | -1.00 | -1.70 | -2.18 | -1.76 | -4.00 |
| flatten | 2 | 20 | -1.00 | - | - | - | -2.00 |

Time from order sent to fill: p50 0.50 s, p95 6.00 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 32 |
| ASML_DUAL | 32 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 29 | 5.66 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.95 ticks, top size 38, trades/min 284.4 | ASML_DUAL: spread 1.84 ticks, top size 53, trades/min 59.8 | crossed 0.00% of time, edge - ticks
