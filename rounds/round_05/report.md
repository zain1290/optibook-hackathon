# Run report: 20261111-000843_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 105)
- Strategy: **evolved**, params {'version': 'v4'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **49.80**, max drawdown 14.35, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 49.80 | 1386 | 11 |
| 2 | team01_quote_hedge | 7.70 | 170 | 7 |
| 3 | team10_cross_arb | 0.80 | 80 | 0 |
| 4 | team00_cross_arb | 0.00 | 0 | 0 |
| 5 | team03_cross_arb | 0.00 | 0 | 0 |
| 6 | team05_cross_arb | 0.00 | 0 | 0 |
| 7 | team08_cross_arb | 0.00 | 0 | 0 |
| 8 | team11_cross_arb | 0.00 | 0 | 0 |
| 9 | team04_quote_hedge | -3.00 | 204 | 10 |
| 10 | team06_quote_hedge | -3.40 | 616 | 10 |
| 11 | team09_quote_hedge | -7.00 | 1074 | 30 |
| 12 | team02_quote_hedge | -7.10 | 1118 | 10 |
| 13 | team07_quote_hedge | -29.20 | 1284 | 20 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.92 | 37.27 | 99.98 | 292.66 | 2145.41 | 0.42 |
| ASML_DUAL | 0.10 | 1.94 | 37.16 | 99.98 | 64.85 | 300.45 | 0.40 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.02 | 1.00 |

### Counterparties (13 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 21037 | 202 | 48.99 |
| ASML | flow_ASML | 18884 | 18884 | 43.97 |
| ASML_DUAL | flow_ASML_DUAL | 2387 | 2387 | 39.69 |
| ASML_DUAL | mm_ASML_DUAL | 717 | 214 | 11.92 |
| ASML_DUAL | us | 698 | 67 | 11.61 |
| ASML | us | 688 | 51 | 1.60 |
| ASML | team07_quote_hedge | 666 | 666 | 1.55 |
| ASML_DUAL | team07_quote_hedge | 618 | 35 | 10.28 |
| ASML | team09_quote_hedge | 573 | 573 | 1.33 |
| ASML | team02_quote_hedge | 561 | 561 | 1.31 |
| ASML_DUAL | team02_quote_hedge | 557 | 77 | 9.26 |
| ASML_DUAL | team09_quote_hedge | 501 | 50 | 8.33 |
| ASML_DUAL | team06_quote_hedge | 308 | 24 | 5.12 |
| ASML | team06_quote_hedge | 308 | 308 | 0.72 |
| ASML_DUAL | team04_quote_hedge | 102 | 37 | 1.70 |
| ASML | team04_quote_hedge | 102 | 102 | 0.24 |
| ASML | team01_quote_hedge | 85 | 85 | 0.20 |
| ASML_DUAL | team01_quote_hedge | 85 | 75 | 1.41 |
| ASML | team10_cross_arb | 40 | 40 | 0.09 |
| ASML_DUAL | team10_cross_arb | 40 | 40 | 0.67 |
| ASML_DUAL | informed_ASML_DUAL | 1 | 1 | 0.02 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 548 | 54.75 |
| delete_order | requote | 530 | 52.96 |
| insert_order | hedge_passive | 174 | 17.39 |
| delete_order | hedge_cancel | 39 | 3.90 |
| insert_order | arb_dual | 5 | 0.50 |
| insert_order | hedge | 5 | 0.50 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.13 |
| delete_order | 0.00 | 0.01 | 0.01 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **15**, average 2.17/s, client-side throttled: 0

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| hedge_passive | 162 | 637 | -0.27 | -0.28 | -0.52 | -0.45 | -17.50 |
| quote | 145 | 631 | 0.51 | 1.01 | 1.37 | 1.44 | 32.10 |
| flatten | 4 | 48 | -0.54 | - | - | - | -2.60 |
| arb_dual | 5 | 43 | 1.00 | 0.51 | 1.05 | 0.62 | 4.30 |
| hedge | 5 | 27 | -1.00 | -0.81 | -1.31 | -2.42 | -2.70 |

Time from order sent to fill: p50 0.40 s, p95 5.30 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 70 |
| ASML_DUAL | 70 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 10 | 8.41 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.92 ticks, top size 37, trades/min 292.7 | ASML_DUAL: spread 1.94 ticks, top size 37, trades/min 64.8 | crossed 0.02% of time, edge 1.00 ticks
