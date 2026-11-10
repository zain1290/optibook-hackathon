# Run report: 20261111-002553_evolved_sim

- Mode: **sim** (scenario crowded_clones, teams 12, seed 110)
- Strategy: **evolved**, params {'version': 'v10'}, loop 0.1s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **48.60**, max drawdown 4.60, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **2/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | team05_clone | 56.00 | 936 | 30 |
| 2 | us | 48.60 | 994 | 30 |
| 3 | team04_clone | 26.10 | 602 | 15 |
| 4 | team00_clone | 21.80 | 560 | 10 |
| 5 | team01_clone | 17.89 | 1071 | 23 |
| 6 | team02_clone | 7.10 | 154 | 20 |
| 7 | team10_quote_hedge | 3.80 | 122 | 5 |
| 8 | team07_quote_hedge | 1.50 | 172 | 0 |
| 9 | team09_cross_arb | 0.00 | 0 | 0 |
| 10 | team11_cross_arb | 0.00 | 0 | 0 |
| 11 | team03_clone | -1.00 | 156 | 20 |
| 12 | team08_quote_hedge | -4.70 | 112 | 20 |
| 13 | team06_quote_hedge | -32.60 | 1304 | 18 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.91 | 37.82 | 99.98 | 296.25 | 2093.76 | 0.41 |
| ASML_DUAL | 0.10 | 1.69 | 43.15 | 99.98 | 62.95 | 278.77 | 0.29 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.03 | 1.00 |

### Counterparties (16 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 19499 | 220 | 46.53 |
| ASML | flow_ASML | 19384 | 19384 | 46.25 |
| ASML_DUAL | flow_ASML_DUAL | 1941 | 1941 | 34.78 |
| ASML | team06_quote_hedge | 663 | 663 | 1.58 |
| ASML_DUAL | team06_quote_hedge | 641 | 106 | 11.49 |
| ASML_DUAL | team01_clone | 546 | 28 | 9.78 |
| ASML | team01_clone | 525 | 134 | 1.25 |
| ASML_DUAL | us | 524 | 132 | 9.39 |
| ASML_DUAL | team05_clone | 483 | 118 | 8.66 |
| ASML_DUAL | mm_ASML_DUAL | 480 | 225 | 8.60 |
| ASML | us | 470 | 112 | 1.12 |
| ASML | team05_clone | 453 | 109 | 1.08 |
| ASML_DUAL | team04_clone | 320 | 45 | 5.73 |
| ASML | team04_clone | 282 | 79 | 0.67 |
| ASML_DUAL | team00_clone | 280 | 5 | 5.02 |
| ASML | team00_clone | 280 | 21 | 0.67 |
| ASML | team07_quote_hedge | 86 | 86 | 0.21 |
| ASML_DUAL | team07_quote_hedge | 86 | 86 | 1.54 |
| ASML_DUAL | team02_clone | 81 | 38 | 1.45 |
| ASML_DUAL | team03_clone | 78 | 8 | 1.40 |
| ASML | team03_clone | 78 | 30 | 0.19 |
| ASML | team02_clone | 73 | 0 | 0.17 |
| ASML | team10_quote_hedge | 61 | 61 | 0.15 |
| ASML_DUAL | team10_quote_hedge | 61 | 46 | 1.09 |
| ASML | team08_quote_hedge | 56 | 56 | 0.13 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 554 | 55.35 |
| delete_order | requote | 544 | 54.35 |
| insert_order | hedge_passive | 161 | 16.09 |
| delete_order | hedge_cancel | 92 | 9.19 |
| insert_order | arb_dual | 18 | 1.80 |
| insert_order | hedge | 14 | 1.40 |
| amend_order | hedge_shrink | 2 | 0.20 |
| delete_orders | - | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.07 |
| delete_order | 0.00 | 0.00 | 0.02 |
| amend_order | 0.01 | 0.01 | 0.01 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **18**, average 2.31/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| quote | 81 | 392 | 0.98 | 0.84 | 0.77 | 0.61 | 38.50 |
| hedge_passive | 86 | 358 | 0.26 | 0.42 | 0.30 | 0.25 | 9.40 |
| arb_dual | 21 | 132 | 1.13 | 0.73 | 0.87 | 0.23 | 14.95 |
| hedge | 16 | 112 | -0.80 | -0.69 | 0.05 | 0.50 | -8.95 |

Time from order sent to fill: p50 0.30 s, p95 4.30 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 30 |
| ASML_DUAL | 24 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 30 | 8.49 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.91 ticks, top size 38, trades/min 296.3 | ASML_DUAL: spread 1.69 ticks, top size 43, trades/min 62.9 | crossed 0.03% of time, edge 1.00 ticks
