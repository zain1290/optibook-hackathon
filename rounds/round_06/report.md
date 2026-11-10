# Run report: 20261111-001338_evolved_sim

- Mode: **sim** (scenario crowded, teams 12, seed 106)
- Strategy: **evolved**, params {'version': 'v6'}, loop 0.15s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **116.80**, max drawdown 21.90, final positions {'ASML': 0, 'ASML_DUAL': 0}
- Pairs (primary, dual): [('ASML', 'ASML_DUAL')]
- Code: 7a3922e dirty=True, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl | volume | max |net delta| |
|---|---|---|---|---|
| 1 | us | 116.80 | 1820 | 30 |
| 2 | team05_cross_arb | 5.00 | 78 | 0 |
| 3 | team07_quote_hedge | 0.70 | 216 | 6 |
| 4 | team10_cross_arb | 0.00 | 0 | 0 |
| 5 | team11_cross_arb | 0.00 | 0 | 0 |
| 6 | team04_quote_hedge | -1.10 | 174 | 5 |
| 7 | team02_quote_hedge | -2.50 | 12 | 5 |
| 8 | team03_quote_hedge | -2.90 | 150 | 27 |
| 9 | team01_quote_hedge | -6.90 | 262 | 8 |
| 10 | team09_quote_hedge | -8.60 | 98 | 20 |
| 11 | team06_quote_hedge | -15.60 | 1502 | 10 |
| 12 | team08_quote_hedge | -16.20 | 358 | 20 |
| 13 | team00_quote_hedge | -27.80 | 1508 | 10 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| ASML | 0.10 | 1.96 | 38.27 | 99.98 | 311.04 | 2242.93 | 0.42 |
| ASML_DUAL | 0.10 | 1.79 | 20.47 | 99.98 | 71.04 | 291.66 | 0.38 |

| pair | % time dual crossed vs primary | mean edge when crossed (ticks) |
|---|---|---|
| ASML/ASML_DUAL | 0.02 | 3.00 |

### Counterparties (15 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| ASML | mm_ASML | 21710 | 55 | 48.36 |
| ASML | flow_ASML | 20055 | 20055 | 44.67 |
| ASML_DUAL | flow_ASML_DUAL | 2165 | 2165 | 37.08 |
| ASML_DUAL | us | 924 | 144 | 15.83 |
| ASML | us | 896 | 103 | 2.00 |
| ASML | team06_quote_hedge | 784 | 784 | 1.75 |
| ASML_DUAL | team00_quote_hedge | 758 | 14 | 12.98 |
| ASML | team00_quote_hedge | 750 | 750 | 1.67 |
| ASML_DUAL | team06_quote_hedge | 718 | 43 | 12.30 |
| ASML_DUAL | mm_ASML_DUAL | 626 | 321 | 10.72 |
| ASML_DUAL | team08_quote_hedge | 179 | 17 | 3.07 |
| ASML | team08_quote_hedge | 179 | 179 | 0.40 |
| ASML | team01_quote_hedge | 131 | 131 | 0.29 |
| ASML_DUAL | team01_quote_hedge | 131 | 81 | 2.24 |
| ASML_DUAL | team07_quote_hedge | 108 | 48 | 1.85 |
| ASML | team07_quote_hedge | 108 | 108 | 0.24 |
| ASML | team03_quote_hedge | 102 | 102 | 0.23 |
| ASML | team04_quote_hedge | 87 | 87 | 0.19 |
| ASML_DUAL | team04_quote_hedge | 87 | 5 | 1.49 |
| ASML_DUAL | team09_quote_hedge | 49 | 3 | 0.84 |
| ASML | team09_quote_hedge | 49 | 49 | 0.11 |
| ASML_DUAL | team03_quote_hedge | 48 | 38 | 0.82 |
| ASML | team05_cross_arb | 39 | 39 | 0.09 |
| ASML_DUAL | team05_cross_arb | 39 | 39 | 0.67 |
| ASML_DUAL | team02_quote_hedge | 6 | 1 | 0.10 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 501 | 50.06 |
| delete_order | requote | 466 | 46.56 |
| insert_order | hedge_passive | 349 | 34.87 |
| delete_order | hedge_cancel | 181 | 18.08 |
| insert_order | hedge | 11 | 1.10 |
| insert_order | arb_dual | 5 | 0.50 |
| delete_orders | - | 2 | 0.20 |
| insert_order | flatten | 2 | 0.20 |
| amend_order | hedge_shrink | 1 | 0.10 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.01 | 0.01 | 0.05 |
| delete_order | 0.00 | 0.00 | 0.02 |
| amend_order | 0.01 | 0.01 | 0.01 |
| delete_orders | 0.01 | 0.01 | 0.01 |

Peak ops in any 1 s window: **20**, average 2.53/s, client-side throttled: 5

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid. Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| hedge_passive | 218 | 793 | 0.58 | 0.44 | 0.46 | 0.35 | 45.60 |
| quote | 193 | 780 | 1.04 | 0.96 | 1.06 | 1.35 | 81.35 |
| flatten | 8 | 124 | -1.52 | - | - | - | -18.80 |
| arb_dual | 9 | 82 | 2.28 | 2.05 | 1.56 | 1.34 | 18.70 |
| hedge | 11 | 41 | -1.00 | -1.12 | -1.16 | -1.20 | -4.10 |

Time from order sent to fill: p50 0.40 s, p95 5.30 s

## Risk

| instrument | max |position| |
|---|---|
| ASML | 64 |
| ASML_DUAL | 64 |

| pair | max |net delta| | % time net delta != 0 |
|---|---|---|
| ASML/ASML_DUAL | 20 | 14.49 |

## Simulator calibration (copy into optisim/scenarios.py)

- ASML: spread 1.96 ticks, top size 38, trades/min 311.0 | ASML_DUAL: spread 1.79 ticks, top size 20, trades/min 71.0 | crossed 0.02% of time, edge 3.00 ticks
