# Run report: 20261110-235502_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 101)
- Strategy: **evolved**, params {'version': 'v0'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **10.60**, max drawdown 7.00, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 10.60 | 428 | 10 |
| 2 | team07_quote_hedge | 9.40 | 392 | 10 |
| 3 | team08_quote_hedge | 7.60 | 104 | 5 |
| 4 | team00_quote_hedge | 4.40 | 298 | 5 |
| 5 | team01_cross_arb | 3.60 | 48 | 0 |
| 6 | team04_quote_hedge | 3.60 | 2610 | 10 |
| 7 | team03_quote_hedge | 1.90 | 798 | 20 |
| 8 | team02_cross_arb | 0.00 | 0 | 0 |
| 9 | team05_cross_arb | 0.00 | 0 | 0 |
| 10 | team06_cross_arb | 0.00 | 0 | 0 |
| 11 | team11_cross_arb | 0.00 | 0 | 0 |
| 12 | team10_quote_hedge | -0.60 | 324 | 10 |
| 13 | team09_buggy | -31.96 | 720 | 94 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 2.00 | 38.59 | 99.98 | 282.66 | 2140.52 | 0.41 |
| ASML_DUAL | 0.10 | 1.87 | 19.26 | 99.98 | 70.14 | 313.94 | 0.35 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.02 | 2.00 |

### Counterparties (13 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 21423 | 0 | 50.00 |
| ASML | flow_ASML | 18957 | 18957 | 44.24 |
| ASML_DUAL | flow_ASML_DUAL | 2250 | 2250 | 35.81 |
| ASML_DUAL | team04_quote_hedge | 1340 | 52 | 21.32 |
| ASML | team04_quote_hedge | 1270 | 1270 | 2.96 |
| ASML_DUAL | mm_ASML_DUAL | 778 | 249 | 12.38 |
| ASML_DUAL | team09_buggy | 720 | 327 | 11.46 |
| ASML_DUAL | team03_quote_hedge | 399 | 10 | 6.35 |
| ASML | team03_quote_hedge | 399 | 399 | 0.93 |
| ASML | us | 214 | 214 | 0.50 |
| ASML_DUAL | us | 214 | 81 | 3.41 |
| ASML_DUAL | team07_quote_hedge | 196 | 81 | 3.12 |
| ASML | team07_quote_hedge | 196 | 196 | 0.46 |
| ASML_DUAL | team10_quote_hedge | 162 | 10 | 2.58 |
| ASML | team10_quote_hedge | 162 | 162 | 0.38 |
| ASML_DUAL | team00_quote_hedge | 149 | 31 | 2.37 |
| ASML | team00_quote_hedge | 149 | 149 | 0.35 |
| ASML_DUAL | team08_quote_hedge | 52 | 27 | 0.83 |
| ASML | team08_quote_hedge | 52 | 52 | 0.12 |
| ASML | team01_cross_arb | 24 | 24 | 0.06 |
| ASML_DUAL | team01_cross_arb | 24 | 24 | 0.38 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 1933 | 193.14 |
| delete_order | requote | 1924 | 192.24 |
| insert_order | hedge | 27 | 2.70 |
| insert_order | arb_dual | 8 | 0.80 |
| insert_order | arb_primary | 8 | 0.80 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.04 |
| delete_order | 0.00 | 0.00 | 0.14 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **20**, average 6.50/s, client-side throttled: 153

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| hedge | 27 | 133 | -1.00 | -1.18 | -1.31 | -1.14 | -13.30 |
| quote | 27 | 133 | 1.44 | 1.62 | 1.77 | 1.81 | 19.10 |
| arb_primary | 8 | 74 | -1.00 | -0.82 | -1.22 | 1.37 | -7.40 |
| arb_dual | 9 | 74 | 1.84 | 1.66 | 2.05 | -0.61 | 13.60 |
| flatten | 2 | 14 | -1.00 | - | - | - | -1.40 |

Time from order sent to fill: p50 0.00 s, p95 2.20 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 43 |
| ASML_DUAL | 43 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 0 | 0.00 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 2.00 ticks, top size 39, trades/min 282.7 | ASML_DUAL: spread 1.87 ticks, top size 19, trades/min 70.1 | crossed 0.02% of time, edge 2.00 ticks
