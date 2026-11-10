# Run report: 20261111-000016_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 103)
- Strategy: **evolved**, params {'version': 'v2'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **62.80**, max drawdown 3.75, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 62.80 | 806 | 13 |
| 2 | team06_quote_hedge | 12.30 | 652 | 5 |
| 3 | team08_quote_hedge | 10.80 | 648 | 10 |
| 4 | team01_quote_hedge | 10.50 | 696 | 10 |
| 5 | team02_cross_arb | 7.40 | 108 | 0 |
| 6 | team10_quote_hedge | 2.30 | 552 | 10 |
| 7 | team00_quote_hedge | 1.60 | 126 | 5 |
| 8 | team05_quote_hedge | 1.60 | 144 | 5 |
| 9 | team03_cross_arb | 0.00 | 0 | 0 |
| 10 | team09_cross_arb | 0.00 | 0 | 0 |
| 11 | team11_cross_arb | 0.00 | 0 | 0 |
| 12 | team04_quote_hedge | -9.20 | 804 | 20 |
| 13 | team07_buggy | -28.37 | 697 | 95 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.95 | 37.82 | 99.98 | 281.67 | 2137.12 | 0.41 |
| ASML_DUAL | 0.10 | 2.47 | 31.50 | 99.98 | 62.95 | 298.15 | 0.36 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.03 | 1.50 |

### Counterparties (14 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 21187 | 165 | 49.53 |
| ASML | flow_ASML | 19345 | 19345 | 45.22 |
| ASML_DUAL | flow_ASML_DUAL | 2142 | 2142 | 35.89 |
| ASML_DUAL | mm_ASML_DUAL | 839 | 174 | 14.06 |
| ASML_DUAL | team07_buggy | 697 | 328 | 11.68 |
| ASML_DUAL | us | 416 | 49 | 6.97 |
| ASML_DUAL | team04_quote_hedge | 403 | 28 | 6.75 |
| ASML | team04_quote_hedge | 401 | 401 | 0.94 |
| ASML | us | 390 | 23 | 0.91 |
| ASML | team01_quote_hedge | 348 | 348 | 0.81 |
| ASML_DUAL | team01_quote_hedge | 348 | 10 | 5.83 |
| ASML_DUAL | team06_quote_hedge | 331 | 83 | 5.55 |
| ASML_DUAL | team08_quote_hedge | 327 | 54 | 5.48 |
| ASML | team06_quote_hedge | 321 | 321 | 0.75 |
| ASML | team08_quote_hedge | 321 | 321 | 0.75 |
| ASML | team10_quote_hedge | 276 | 276 | 0.65 |
| ASML_DUAL | team10_quote_hedge | 276 | 10 | 4.62 |
| ASML_DUAL | team05_quote_hedge | 72 | 10 | 1.21 |
| ASML | team05_quote_hedge | 72 | 72 | 0.17 |
| ASML_DUAL | team00_quote_hedge | 63 | 42 | 1.06 |
| ASML | team00_quote_hedge | 63 | 63 | 0.15 |
| ASML | team02_cross_arb | 54 | 54 | 0.13 |
| ASML_DUAL | team02_cross_arb | 54 | 54 | 0.90 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 619 | 61.85 |
| delete_order | requote | 608 | 60.75 |
| insert_order | hedge_passive | 99 | 9.89 |
| delete_order | hedge_cancel | 21 | 2.10 |
| insert_order | arb_dual | 6 | 0.60 |
| insert_order | hedge | 4 | 0.40 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.03 |
| delete_order | 0.00 | 0.00 | 0.04 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **20**, average 2.27/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| quote | 81 | 367 | 1.26 | 1.65 | 1.99 | 1.75 | 46.35 |
| hedge_passive | 90 | 367 | -0.37 | -0.23 | -0.44 | -0.33 | -13.70 |
| arb_dual | 7 | 45 | 2.27 | 1.64 | 1.62 | 1.53 | 10.20 |
| hedge | 4 | 19 | -1.00 | -0.26 | -0.26 | 1.37 | -1.90 |
| flatten | 2 | 8 | -1.00 | - | - | - | -0.80 |

Time from order sent to fill: p50 0.50 s, p95 4.90 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 24 |
| ASML_DUAL | 24 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 10 | 6.08 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.95 ticks, top size 38, trades/min 281.7 | ASML_DUAL: spread 2.47 ticks, top size 31, trades/min 62.9 | crossed 0.03% of time, edge 1.50 ticks
