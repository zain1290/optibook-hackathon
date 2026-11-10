# Run report: 20261111-002348_evolved_sim

- Mode: **sim** (scenario crowded_clones, teams 12, seed 109)
- Strategy: **evolved**, params {'version': 'v9'}, loop 0.1s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **82.95**, max drawdown 8.70, final positions {'ASML': -7, 'ASML_DUAL': 7}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 82.60 | 1162 | 18 |
| 2 | team05_clone | 74.20 | 1518 | 16 |
| 3 | team02_clone | 55.90 | 826 | 10 |
| 4 | team01_clone | 53.40 | 725 | 12 |
| 5 | team00_clone | 6.30 | 136 | 10 |
| 6 | team03_clone | 3.90 | 50 | 14 |
| 7 | team04_clone | 2.80 | 36 | 3 |
| 8 | team06_cross_arb | 0.00 | 0 | 0 |
| 9 | team07_cross_arb | 0.00 | 0 | 0 |
| 10 | team09_cross_arb | 0.00 | 0 | 0 |
| 11 | team11_quote_hedge | -1.00 | 182 | 5 |
| 12 | team08_quote_hedge | -2.00 | 48 | 10 |
| 13 | team10_quote_hedge | -8.00 | 234 | 20 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.89 | 37.11 | 99.98 | 296.05 | 2020.02 | 0.42 |
| ASML_DUAL | 0.10 | 2.07 | 27.72 | 99.98 | 70.64 | 261.78 | 0.34 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.02 | 1.00 |

### Counterparties (14 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | flow_ASML | 19289 | 19289 | 47.70 |
| ASML | mm_ASML | 18768 | 173 | 46.42 |
| ASML_DUAL | flow_ASML_DUAL | 2074 | 2074 | 39.58 |
| ASML_DUAL | team05_clone | 796 | 25 | 15.19 |
| ASML | team05_clone | 722 | 171 | 1.79 |
| ASML_DUAL | mm_ASML_DUAL | 626 | 148 | 11.95 |
| ASML_DUAL | us | 599 | 64 | 11.43 |
| ASML | us | 563 | 122 | 1.39 |
| ASML_DUAL | team02_clone | 428 | 87 | 8.17 |
| ASML | team02_clone | 398 | 111 | 0.98 |
| ASML_DUAL | team01_clone | 378 | 54 | 7.21 |
| ASML | team01_clone | 347 | 82 | 0.86 |
| ASML | team10_quote_hedge | 121 | 121 | 0.30 |
| ASML_DUAL | team10_quote_hedge | 113 | 66 | 2.16 |
| ASML_DUAL | team11_quote_hedge | 91 | 48 | 1.74 |
| ASML | team11_quote_hedge | 91 | 91 | 0.23 |
| ASML_DUAL | team00_clone | 68 | 14 | 1.30 |
| ASML | team00_clone | 68 | 25 | 0.17 |
| ASML_DUAL | team03_clone | 25 | 20 | 0.48 |
| ASML | team03_clone | 25 | 2 | 0.06 |
| ASML_DUAL | team08_quote_hedge | 24 | 14 | 0.46 |
| ASML | team08_quote_hedge | 24 | 24 | 0.06 |
| ASML | team04_clone | 18 | 6 | 0.04 |
| ASML_DUAL | team04_clone | 18 | 6 | 0.34 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 561 | 56.05 |
| delete_order | requote | 541 | 54.05 |
| insert_order | hedge_passive | 242 | 24.18 |
| delete_order | hedge_cancel | 137 | 13.69 |
| insert_order | hedge | 31 | 3.10 |
| insert_order | arb_dual | 10 | 1.00 |
| amend_order | hedge_shrink | 2 | 0.20 |
| delete_orders | - | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.07 |
| delete_order | 0.00 | 0.00 | 0.01 |
| amend_order | 0.02 | 0.02 | 0.02 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **17**, average 2.54/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| quote | 141 | 535 | 1.22 | 1.26 | 1.19 | 1.57 | 65.05 |
| hedge_passive | 129 | 441 | 0.39 | 0.56 | 0.44 | -0.01 | 17.15 |
| hedge | 38 | 122 | -0.65 | -0.78 | -1.22 | -0.36 | -7.90 |
| arb_dual | 13 | 64 | 1.25 | 1.11 | 0.94 | 0.44 | 8.00 |

Time from order sent to fill: p50 0.30 s, p95 6.20 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 58 |
| ASML_DUAL | 58 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 18 | 10.16 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.89 ticks, top size 37, trades/min 296.1 | ASML_DUAL: spread 2.07 ticks, top size 28, trades/min 70.6 | crossed 0.02% of time, edge 1.00 ticks
