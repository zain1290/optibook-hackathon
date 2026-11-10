# Run report: 20261111-001740_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 108)
- Strategy: **evolved**, params {'version': 'v8'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **102.10**, max drawdown 6.00, final positions {'ASML': 5, 'ASML_DUAL': -5}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 102.10 | 1570 | 17 |
| 2 | team08_quote_hedge | 6.40 | 152 | 1 |
| 3 | team10_cross_arb | 4.40 | 100 | 0 |
| 4 | team01_cross_arb | 2.00 | 102 | 0 |
| 5 | team07_cross_arb | 0.00 | 0 | 0 |
| 6 | team11_quote_hedge | 0.00 | 138 | 5 |
| 7 | team03_quote_hedge | -0.20 | 66 | 10 |
| 8 | team09_quote_hedge | -2.70 | 416 | 10 |
| 9 | team04_quote_hedge | -3.30 | 308 | 25 |
| 10 | team05_quote_hedge | -3.40 | 292 | 20 |
| 11 | team00_quote_hedge | -12.61 | 389 | 10 |
| 12 | team02_quote_hedge | -26.00 | 1664 | 5 |
| 13 | team06_buggy | -123.36 | 652 | 92 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.93 | 37.38 | 99.98 | 293.36 | 2156.50 | 0.41 |
| ASML_DUAL | 0.10 | 1.75 | 21.92 | 99.98 | 71.54 | 300.05 | 0.34 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.00 | - |

### Counterparties (16 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 20968 | 89 | 48.58 |
| ASML | flow_ASML | 19598 | 19598 | 45.40 |
| ASML_DUAL | flow_ASML_DUAL | 2103 | 2103 | 35.01 |
| ASML_DUAL | team02_quote_hedge | 839 | 40 | 13.97 |
| ASML | team02_quote_hedge | 825 | 825 | 1.91 |
| ASML_DUAL | us | 803 | 59 | 13.37 |
| ASML | us | 767 | 63 | 1.78 |
| ASML_DUAL | mm_ASML_DUAL | 654 | 197 | 10.89 |
| ASML_DUAL | team06_buggy | 652 | 325 | 10.86 |
| ASML_DUAL | team09_quote_hedge | 208 | 0 | 3.46 |
| ASML | team09_quote_hedge | 208 | 208 | 0.48 |
| ASML_DUAL | team00_quote_hedge | 196 | 16 | 3.26 |
| ASML | team00_quote_hedge | 193 | 193 | 0.45 |
| ASML | team04_quote_hedge | 182 | 182 | 0.42 |
| ASML_DUAL | team05_quote_hedge | 146 | 28 | 2.43 |
| ASML | team05_quote_hedge | 146 | 146 | 0.34 |
| ASML_DUAL | team04_quote_hedge | 126 | 40 | 2.10 |
| ASML | team08_quote_hedge | 76 | 76 | 0.18 |
| ASML_DUAL | team08_quote_hedge | 76 | 55 | 1.27 |
| ASML_DUAL | team11_quote_hedge | 69 | 34 | 1.15 |
| ASML | team11_quote_hedge | 69 | 69 | 0.16 |
| ASML | team01_cross_arb | 51 | 51 | 0.12 |
| ASML_DUAL | team01_cross_arb | 51 | 51 | 0.85 |
| ASML | team10_cross_arb | 50 | 50 | 0.12 |
| ASML_DUAL | team10_cross_arb | 50 | 50 | 0.83 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 535 | 53.46 |
| delete_order | requote | 509 | 50.86 |
| insert_order | hedge_passive | 336 | 33.57 |
| delete_order | hedge_cancel | 171 | 17.09 |
| insert_order | hedge | 14 | 1.40 |
| insert_order | arb_dual | 7 | 0.70 |
| delete_orders | - | 2 | 0.20 |
| amend_order | hedge_shrink | 1 | 0.10 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.05 |
| delete_order | 0.00 | 0.00 | 0.04 |
| amend_order | 0.00 | 0.00 | 0.00 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **19**, average 2.62/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| quote | 189 | 744 | 1.01 | 1.12 | 1.31 | 1.71 | 74.85 |
| hedge_passive | 214 | 704 | 0.31 | 0.32 | -0.08 | -0.40 | 21.65 |
| hedge | 14 | 63 | -1.00 | -0.61 | -0.23 | -0.65 | -6.30 |
| arb_dual | 9 | 59 | 1.00 | 0.38 | 1.53 | 1.87 | 5.90 |

Time from order sent to fill: p50 0.40 s, p95 4.50 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 56 |
| ASML_DUAL | 58 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 17 | 15.49 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.93 ticks, top size 37, trades/min 293.4 | ASML_DUAL: spread 1.75 ticks, top size 22, trades/min 71.5 | crossed 0.00% of time, edge - ticks
