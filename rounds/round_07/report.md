# Run report: 20261111-001536_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 107)
- Strategy: **evolved**, params {'version': 'v7'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **200.70**, max drawdown 73.90, final positions {'ASML': -10, 'ASML_DUAL': 10}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 199.20 | 2554 | 29 |
| 2 | team01_cross_arb | 20.30 | 72 | 0 |
| 3 | team00_cross_arb | 11.30 | 162 | 0 |
| 4 | team09_quote_hedge | 6.70 | 536 | 49 |
| 5 | team07_cross_arb | 4.90 | 98 | 0 |
| 6 | team05_cross_arb | 0.00 | 0 | 0 |
| 7 | team08_cross_arb | 0.00 | 0 | 0 |
| 8 | team10_quote_hedge | -10.90 | 330 | 10 |
| 9 | team04_quote_hedge | -15.40 | 500 | 30 |
| 10 | team06_quote_hedge | -21.40 | 580 | 48 |
| 11 | team02_quote_hedge | -51.80 | 776 | 35 |
| 12 | team03_quote_hedge | -55.10 | 862 | 28 |
| 13 | team11_buggy | -139.19 | 597 | 92 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.89 | 36.78 | 99.98 | 294.15 | 2171.99 | 0.49 |
| ASML_DUAL | 0.10 | 2.32 | 31.06 | 99.98 | 74.34 | 349.31 | 0.39 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.07 | 3.25 |

### Counterparties (16 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 20849 | 221 | 47.96 |
| ASML | flow_ASML | 19256 | 19256 | 44.29 |
| ASML_DUAL | flow_ASML_DUAL | 2357 | 2357 | 33.71 |
| ASML_DUAL | us | 1342 | 171 | 19.19 |
| ASML | us | 1212 | 102 | 2.79 |
| ASML_DUAL | mm_ASML_DUAL | 927 | 272 | 13.26 |
| ASML_DUAL | team11_buggy | 597 | 283 | 8.54 |
| ASML | team03_quote_hedge | 466 | 466 | 1.07 |
| ASML | team02_quote_hedge | 427 | 427 | 0.98 |
| ASML_DUAL | team03_quote_hedge | 396 | 15 | 5.66 |
| ASML_DUAL | team02_quote_hedge | 349 | 5 | 4.99 |
| ASML | team06_quote_hedge | 338 | 338 | 0.78 |
| ASML | team09_quote_hedge | 317 | 317 | 0.73 |
| ASML | team04_quote_hedge | 280 | 280 | 0.64 |
| ASML_DUAL | team06_quote_hedge | 242 | 34 | 3.46 |
| ASML_DUAL | team04_quote_hedge | 220 | 29 | 3.15 |
| ASML_DUAL | team09_quote_hedge | 219 | 78 | 3.13 |
| ASML | team10_quote_hedge | 165 | 165 | 0.38 |
| ASML_DUAL | team10_quote_hedge | 165 | 74 | 2.36 |
| ASML | team00_cross_arb | 81 | 81 | 0.19 |
| ASML_DUAL | team00_cross_arb | 81 | 81 | 1.16 |
| ASML | team07_cross_arb | 49 | 49 | 0.11 |
| ASML_DUAL | team07_cross_arb | 49 | 49 | 0.70 |
| ASML | team01_cross_arb | 36 | 36 | 0.08 |
| ASML_DUAL | team01_cross_arb | 36 | 36 | 0.51 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 536 | 53.56 |
| delete_order | requote | 485 | 48.46 |
| insert_order | hedge_passive | 446 | 44.56 |
| delete_order | hedge_cancel | 212 | 21.18 |
| insert_order | hedge | 21 | 2.10 |
| insert_order | arb_dual | 13 | 1.30 |
| amend_order | hedge_shrink | 5 | 0.50 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 1 | 0.10 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.07 |
| delete_order | 0.00 | 0.00 | 0.01 |
| amend_order | 0.01 | 0.03 | 0.03 |
| delete_orders | 0.00 | 0.00 | 0.00 |

Peak ops in any 1 s window: **18**, average 2.87/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| quote | 277 | 1171 | 0.98 | 1.19 | 1.21 | 1.20 | 114.90 |
| hedge_passive | 297 | 1110 | 0.09 | 0.01 | 0.03 | -0.22 | 9.80 |
| arb_dual | 18 | 171 | 3.17 | 3.51 | 3.33 | 5.15 | 54.15 |
| hedge | 21 | 100 | -1.00 | -0.68 | -0.85 | -1.29 | -10.00 |
| flatten | 1 | 2 | -2.00 | - | - | - | -0.40 |

Time from order sent to fill: p50 0.40 s, p95 4.60 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 81 |
| ASML_DUAL | 81 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 28 | 21.15 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.89 ticks, top size 37, trades/min 294.2 | ASML_DUAL: spread 2.32 ticks, top size 31, trades/min 74.3 | crossed 0.07% of time, edge 3.25 ticks
