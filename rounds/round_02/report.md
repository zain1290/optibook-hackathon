# Run report: 20261110-235818_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 102)
- Strategy: **evolved**, params {'version': 'v1'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **-10.20**, max drawdown 11.60, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **10/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | team03_cross_arb | 43.40 | 246 | 0 |
| 2 | team08_quote_hedge | 10.20 | 338 | 20 |
| 3 | team04_cross_arb | 3.00 | 20 | 0 |
| 4 | team02_cross_arb | 2.00 | 40 | 0 |
| 5 | team09_cross_arb | 1.00 | 20 | 0 |
| 6 | team00_cross_arb | 0.00 | 0 | 0 |
| 7 | team06_cross_arb | 0.00 | 0 | 0 |
| 8 | team10_cross_arb | 0.00 | 0 | 0 |
| 9 | team05_quote_hedge | -7.90 | 1920 | 5 |
| 10 | us | -10.20 | 202 | 31 |
| 11 | team11_quote_hedge | -22.60 | 2092 | 10 |
| 12 | team07_quote_hedge | -26.60 | 330 | 20 |
| 13 | team01_quote_hedge | -34.20 | 376 | 20 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.99 | 38.43 | 99.98 | 300.25 | 2149.71 | 0.43 |
| ASML_DUAL | 0.10 | 1.96 | 19.48 | 99.98 | 70.44 | 281.07 | 0.47 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.00 | - |

### Counterparties (15 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 21483 | 7 | 49.93 |
| ASML | flow_ASML | 18723 | 18723 | 43.51 |
| ASML_DUAL | flow_ASML_DUAL | 2194 | 2194 | 39.00 |
| ASML_DUAL | team11_quote_hedge | 1061 | 43 | 18.86 |
| ASML | team11_quote_hedge | 1031 | 1031 | 2.40 |
| ASML_DUAL | team05_quote_hedge | 964 | 43 | 17.13 |
| ASML | team05_quote_hedge | 956 | 956 | 2.22 |
| ASML_DUAL | mm_ASML_DUAL | 669 | 219 | 11.89 |
| ASML | team08_quote_hedge | 189 | 189 | 0.44 |
| ASML | team01_quote_hedge | 188 | 188 | 0.44 |
| ASML_DUAL | team01_quote_hedge | 188 | 14 | 3.34 |
| ASML_DUAL | team07_quote_hedge | 165 | 30 | 2.93 |
| ASML | team07_quote_hedge | 165 | 165 | 0.38 |
| ASML_DUAL | team08_quote_hedge | 149 | 75 | 2.65 |
| ASML | us | 132 | 93 | 0.31 |
| ASML | team03_cross_arb | 123 | 123 | 0.29 |
| ASML_DUAL | team03_cross_arb | 123 | 123 | 2.19 |
| ASML_DUAL | us | 70 | 29 | 1.24 |
| ASML | team02_cross_arb | 20 | 20 | 0.05 |
| ASML_DUAL | team02_cross_arb | 20 | 20 | 0.36 |
| ASML | team04_cross_arb | 10 | 10 | 0.02 |
| ASML_DUAL | team04_cross_arb | 10 | 10 | 0.18 |
| ASML | team09_cross_arb | 10 | 10 | 0.02 |
| ASML_DUAL | team09_cross_arb | 10 | 10 | 0.18 |
| ASML_DUAL | informed_ASML_DUAL | 3 | 3 | 0.05 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 1855 | 185.35 |
| delete_order | requote | 1851 | 184.95 |
| insert_order | hedge_passive | 14 | 1.40 |
| insert_order | arb_dual | 5 | 0.50 |
| insert_order | arb_primary | 5 | 0.50 |
| delete_order | hedge_cancel | 3 | 0.30 |
| insert_order | hedge | 2 | 0.20 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |

| reject reason | count |
|---|---|
| insert_order: would self-trade | 1 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.08 |
| delete_order | 0.00 | 0.00 | 0.10 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **20**, average 6.23/s, client-side throttled: 106

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| arb_primary | 5 | 50 | -0.69 | -0.86 | 0.02 | -0.58 | -3.45 |
| quote | 12 | 41 | -0.59 | -0.30 | -1.49 | -1.87 | -2.40 |
| hedge_passive | 15 | 39 | 0.17 | 0.09 | 1.41 | 1.73 | 0.65 |
| hedge | 2 | 33 | -1.00 | -0.97 | -1.06 | -0.18 | -3.30 |
| flatten | 2 | 20 | -1.50 | - | - | - | -3.00 |
| arb_dual | 4 | 19 | 1.00 | 0.63 | -1.68 | -1.74 | 1.90 |

Time from order sent to fill: p50 0.30 s, p95 2.80 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 10 |
| ASML_DUAL | 10 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 7 | 1.00 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.99 ticks, top size 38, trades/min 300.2 | ASML_DUAL: spread 1.96 ticks, top size 19, trades/min 70.4 | crossed 0.00% of time, edge - ticks
