# Run report: 20261111-212611_combo_sim

- Mode: **sim** (scenario bonafide, teams 12, seed 0)
- Strategy: **combo**, params {}, loop 0.1s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **2931.00**, max drawdown 59.50, final positions {'AMD': 0, 'AVGO': 0, 'NVDA': 0, 'MU': 0, 'SNDK': 0, 'CRWV': 0, 'NBIS': 0, 'VRT': 0}
- Hourly Sharpe (our estimate of the leaderboard number): **22.18**, reconnects: 0, news posts: 9
- Code: 1e0a0ad dirty=False, optibook None

## Leaderboard (sim): we are **2/13**

| rank | team | pnl (fair) | pnl (last price) | hourly sharpe | volume |
|---|---|---|---|---|---|
| 1 | team06_mm | 2939.19 | 2929.50 | 24.63 | 29465 |
| 2 | us | 2931.00 | 2931.00 | 24.09 | 29930 |
| 3 | team10_naive | 754.89 | 713.00 | 0.78 | 3915 |
| 4 | team07_news | 174.00 | 174.00 | 5.66 | 360 |
| 5 | team02_mm | -72.38 | -73.50 | -1.36 | 925 |
| 6 | team09_naive | -73.19 | -83.00 | -2.02 | 610 |
| 7 | team08_mm | -143.82 | -142.50 | -2.48 | 1825 |
| 8 | team05_mm | -223.40 | -215.50 | -0.69 | 8585 |
| 9 | team00_mm | -1281.15 | -1284.00 | -14.23 | 10410 |
| 10 | team11_naive | -2308.08 | -2277.00 | -5.30 | 20935 |
| 11 | team01_naive | -3798.75 | -3786.00 | -8.04 | 21620 |
| 12 | team03_naive | -4004.18 | -3993.00 | -10.87 | 23175 |
| 13 | team04_naive | -5230.07 | -5182.00 | -6.88 | 25930 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| AMD | 0.10 | 1.23 | 583.60 | 99.97 | 85.13 | 2126.23 | 0.84 |
| AVGO | 0.10 | 1.28 | 417.48 | 99.97 | 166.96 | 3301.75 | 0.93 |
| CRWV | 0.10 | 1.29 | 71.64 | 99.97 | 121.20 | 2170.19 | 0.97 |
| MU | 0.10 | 1.23 | 950.53 | 99.97 | 28.18 | 775.85 | 0.70 |
| NBIS | 0.10 | 1.25 | 64.61 | 99.97 | 56.25 | 1044.13 | 0.69 |
| NVDA | 0.10 | 1.23 | 528.90 | 99.97 | 61.65 | 1453.79 | 0.75 |
| SNDK | 0.10 | 1.20 | 104.14 | 99.97 | 28.38 | 492.59 | 0.55 |
| VRT | 0.10 | 1.87 | 2803.47 | 99.97 | 16.19 | 310.74 | 0.70 |

### Counterparties (17 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| AMD | GroovyGrapefruits | 10915 | 9620 | 25.65 |
| AVGO | GroovyGrapefruits | 10855 | 8630 | 16.42 |
| AVGO | team06_mm | 9780 | 9530 | 14.80 |
| AVGO | us | 9760 | 9710 | 14.77 |
| CRWV | us | 8450 | 8440 | 19.45 |
| CRWV | team06_mm | 8025 | 7965 | 18.47 |
| AVGO | team04_naive | 7280 | 900 | 11.02 |
| AVGO | team01_naive | 6200 | 890 | 9.38 |
| NVDA | GroovyGrapefruits | 6160 | 5185 | 21.17 |
| CRWV | team03_naive | 6015 | 460 | 13.85 |
| AMD | team04_naive | 5570 | 600 | 13.09 |
| AVGO | team03_naive | 5540 | 580 | 8.38 |
| AVGO | team11_naive | 4990 | 900 | 7.55 |
| MU | GroovyGrapefruits | 4945 | 4270 | 31.84 |
| CRWV | team11_naive | 4915 | 710 | 11.31 |
| AMD | team03_naive | 4370 | 300 | 10.27 |
| AMD | team11_naive | 4070 | 300 | 9.56 |
| NVDA | team01_naive | 4050 | 300 | 13.92 |
| AVGO | team00_mm | 4000 | 0 | 6.05 |
| CRWV | team04_naive | 3985 | 660 | 9.17 |
| CRWV | team01_naive | 3980 | 125 | 9.16 |
| AMD | us | 3900 | 3880 | 9.16 |
| AMD | team06_mm | 3845 | 3740 | 9.03 |
| NBIS | us | 3720 | 3710 | 17.80 |
| AMD | team01_naive | 3530 | 300 | 8.29 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 3318 | 331.52 |
| delete_order | cancel_stale | 2590 | 258.78 |
| insert_order | take | 1667 | 166.56 |
| delete_order | requote | 695 | 69.44 |
| amend_order | resize | 136 | 13.59 |
| delete_orders | news_pull | 11 | 1.10 |
| delete_orders | - | 8 | 0.80 |
| insert_order | flatten | 7 | 0.70 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.04 | 0.07 | 7.28 |
| delete_order | 0.01 | 0.02 | 0.10 |
| amend_order | 0.01 | 0.02 | 0.05 |
| delete_orders | 0.02 | 0.03 | 0.03 |

Peak ops in any 1 s window: **24**, average 14.04/s, client-side throttled: 29935

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid (dual listing) or the deep mid, where at least 200 lots sit on each side (stocks). Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| take | 1768 | 29730 | 1.33 | 1.08 | 0.95 | 1.17 | 3947.75 |
| quote | 9 | 110 | -0.14 | -0.55 | -0.77 | -2.05 | -1.50 |
| flatten | 8 | 90 | -0.86 | - | - | - | -7.75 |

By instrument (edge x volume at the moment of the fill, in currency):

| instrument | volume | edge x volume |
|---|---|---|
| CRWV | 8450 | 1504.00 |
| AVGO | 9760 | 1161.00 |
| NBIS | 3720 | 470.50 |
| AMD | 3900 | 381.00 |
| NVDA | 2800 | 271.00 |
| SNDK | 1280 | 151.00 |
| MU | 20 | -0.00 |

Time from order sent to fill: p50 0.00 s, p95 0.00 s

## Risk

| instrument | max abs position |
|---|---|
| AMD | 25 |
| AVGO | 45 |
| CRWV | 180 |
| MU | 10 |
| NBIS | 120 |
| NVDA | 20 |
| SNDK | 40 |
| VRT | 0 |

| pair | max abs net delta | % time net delta not 0 |
|---|---|---|

## News impact (11 post x instrument pairs)

| t (s) | instrument | sentiment | move 1s | move 5s | move 30s | post |
|---|---|---|---|---|---|---|
| 13.0 | NVDA | +0 | -1.0 | +3.0 | +11.0 | Retail investors keep talking about NVDA on forums |
| 82.4 | CRWV | +2 | +16.0 | +16.0 | +8.0 | Analyst upgrades CRWV to Strong Buy, sees 30% upside |
| 121.7 | AMD | +2 | -1.0 | +25.0 | +32.0 | AMD smashes earnings expectations, raises full-year guidance |
| 207.0 | MU | -2 | -13.0 | -14.0 | -21.0 | Short seller publishes report questioning MU accounting |
| 252.9 | VRT | -2 | -10.5 | -9.5 | -11.5 | VRT misses revenue estimates, shares slide after hours |
| 337.9 | NVDA | +1 | +1.5 | +20.0 | +6.0 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 337.9 | AMD | +1 | +0.0 | +1.5 | -10.5 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 337.9 | AVGO | +1 | +0.0 | +2.5 | +5.5 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 426.7 | NBIS | -1 | +0.0 | -8.0 | -11.0 | Export restrictions could hit NBIS sales, sources say |
| 511.5 | NBIS | +2 | -0.5 | +17.5 | +17.5 | NBIS smashes earnings expectations, raises full-year guidance |
| 592.1 | NVDA | +0 | +0.5 | -6.0 | -6.0 | NVDA CEO spotted at coffee shop, says 'busy times' |

- 1s after a post with a clear sentiment, price moved **+4.39 ticks** in the direction of the words on average (n=9, 44% of the time the right way)
- 5s after a post with a clear sentiment, price moved **+12.67 ticks** in the direction of the words on average (n=9, 100% of the time the right way)
- 30s after a post with a clear sentiment, price moved **+11.33 ticks** in the direction of the words on average (n=9, 89% of the time the right way)

Rule of thumb: switch news trading on (news_trade_size 20-50) only if the 5s number is clearly bigger than half the spread and right more than ~65% of the time.

## Simulator calibration (copy into optisim/scenarios.py)

Stocks: name: (price, maker half-spread in ticks, top-of-book size, trades/min). Compare with BONA_FIDE.

- AMD: (165.47, 0.61, 584, 85.1)
- AVGO: (209.04, 0.64, 417, 167.0)
- CRWV: (144.21, 0.65, 72, 121.2)
- MU: (77.92, 0.61, 951, 28.2)
- NBIS: (94.56, 0.62, 65, 56.3)
- NVDA: (127.67, 0.61, 529, 61.6)
- SNDK: (54.01, 0.60, 104, 28.4)
- VRT: (64.25, 0.93, 2803, 16.2)
