# Run report: 20261111-215916_combo_sim

- Mode: **sim** (scenario bonafide, teams 12, seed 0)
- Strategy: **combo**, params {}, loop 0.1s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **2379.00**, max drawdown 102.50, final positions {'AMD': 0, 'AVGO': 0, 'NVDA': 0, 'MU': 0, 'SNDK': 0, 'CRWV': 0, 'NBIS': 0, 'VRT': 0}
- Hourly Sharpe (our estimate of the leaderboard number): **23.38**, reconnects: 0, news posts: 9
- Code: a400740 dirty=False, optibook None

## Leaderboard (sim): we are **1/13**

| rank | team | pnl (fair) | pnl (last price) | hourly sharpe | volume |
|---|---|---|---|---|---|
| 1 | us | 2379.00 | 2379.00 | 21.14 | 29390 |
| 2 | team06_mm | 2362.26 | 2363.50 | 20.96 | 30350 |
| 3 | team07_news | 165.00 | 165.00 | 5.26 | 360 |
| 4 | team02_mm | -40.09 | -43.00 | -1.93 | 975 |
| 5 | team09_naive | -70.40 | -82.00 | -0.21 | 630 |
| 6 | team08_mm | -139.25 | -142.00 | -2.37 | 2015 |
| 7 | team10_naive | -600.08 | -566.00 | -1.69 | 3625 |
| 8 | team05_mm | -712.58 | -775.50 | -3.72 | 7850 |
| 9 | team00_mm | -1104.40 | -1127.00 | -20.75 | 10245 |
| 10 | team03_naive | -1616.92 | -1569.50 | -3.78 | 20205 |
| 11 | team04_naive | -3163.44 | -3239.00 | -5.69 | 26010 |
| 12 | team11_naive | -3940.18 | -3895.50 | -8.74 | 21130 |
| 13 | team01_naive | -4319.94 | -4287.50 | -6.36 | 21205 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| AMD | 0.10 | 1.24 | 600.34 | 99.97 | 90.12 | 2237.64 | 0.84 |
| AVGO | 0.10 | 1.29 | 410.81 | 99.97 | 170.06 | 3226.31 | 0.93 |
| CRWV | 0.10 | 1.25 | 68.16 | 99.97 | 116.50 | 1947.38 | 0.97 |
| MU | 0.10 | 1.23 | 943.74 | 99.97 | 26.28 | 691.92 | 0.69 |
| NBIS | 0.10 | 1.23 | 73.84 | 99.97 | 57.95 | 1077.60 | 0.73 |
| NVDA | 0.10 | 1.22 | 517.13 | 99.97 | 59.35 | 1347.38 | 0.75 |
| SNDK | 0.10 | 1.18 | 95.07 | 99.97 | 27.58 | 514.57 | 0.59 |
| VRT | 0.10 | 1.87 | 2808.35 | 99.97 | 15.69 | 307.74 | 0.70 |

### Counterparties (17 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| AMD | GroovyGrapefruits | 11435 | 10170 | 25.53 |
| AVGO | us | 10250 | 10145 | 15.87 |
| AVGO | team06_mm | 10235 | 10010 | 15.85 |
| AVGO | GroovyGrapefruits | 9325 | 7905 | 14.44 |
| CRWV | team06_mm | 7830 | 7745 | 20.09 |
| CRWV | us | 7760 | 7760 | 19.91 |
| AVGO | team04_naive | 7740 | 1190 | 11.99 |
| AVGO | team03_naive | 5450 | 300 | 8.44 |
| CRWV | team04_naive | 5395 | 430 | 13.84 |
| NVDA | GroovyGrapefruits | 5180 | 4740 | 19.21 |
| AMD | team01_naive | 5080 | 300 | 11.34 |
| AVGO | team11_naive | 5070 | 600 | 7.85 |
| AMD | team04_naive | 5070 | 600 | 11.32 |
| AVGO | team01_naive | 4960 | 300 | 7.68 |
| MU | GroovyGrapefruits | 4535 | 4095 | 32.74 |
| CRWV | team03_naive | 4265 | 175 | 10.94 |
| AMD | team06_mm | 4215 | 4090 | 9.41 |
| AVGO | team00_mm | 3930 | 0 | 6.09 |
| AMD | us | 3850 | 3840 | 8.60 |
| CRWV | team01_naive | 3825 | 175 | 9.81 |
| AMD | team11_naive | 3790 | 600 | 8.46 |
| NBIS | team06_mm | 3755 | 3680 | 17.41 |
| NVDA | team01_naive | 3610 | 0 | 13.39 |
| NBIS | us | 3590 | 3550 | 16.64 |
| CRWV | team11_naive | 3550 | 170 | 9.11 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 3360 | 335.72 |
| delete_order | cancel_stale | 2637 | 263.48 |
| insert_order | take | 1631 | 162.96 |
| delete_order | requote | 684 | 68.34 |
| amend_order | resize | 130 | 12.99 |
| delete_orders | news_pull | 11 | 1.10 |
| delete_orders | - | 8 | 0.80 |
| insert_order | flatten | 6 | 0.60 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.04 | 0.08 | 1.07 |
| delete_order | 0.01 | 0.02 | 1.20 |
| amend_order | 0.01 | 0.02 | 0.05 |
| delete_orders | 0.02 | 0.03 | 0.03 |

Peak ops in any 1 s window: **25**, average 14.10/s, client-side throttled: 29165

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid (dual listing) or the deep mid, where at least 200 lots sit on each side (stocks). Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| take | 1739 | 29050 | 1.31 | 1.04 | 0.88 | 0.93 | 3797.75 |
| quote | 18 | 210 | -0.39 | -0.85 | -0.79 | 0.61 | -8.25 |
| flatten | 8 | 130 | -1.23 | - | - | - | -16.00 |

By instrument (edge x volume at the moment of the fill, in currency):

| instrument | volume | edge x volume |
|---|---|---|
| CRWV | 7760 | 1322.50 |
| AVGO | 10250 | 1220.50 |
| NBIS | 3590 | 445.50 |
| AMD | 3850 | 383.00 |
| NVDA | 2700 | 258.50 |
| SNDK | 1240 | 143.50 |

Time from order sent to fill: p50 0.00 s, p95 0.00 s

## Risk

| instrument | max abs position |
|---|---|
| AMD | 20 |
| AVGO | 55 |
| CRWV | 100 |
| MU | 0 |
| NBIS | 100 |
| NVDA | 20 |
| SNDK | 40 |
| VRT | 0 |

| pair | max abs net delta | % time net delta not 0 |
|---|---|---|

## News impact (11 post x instrument pairs)

| t (s) | instrument | sentiment | move 1s | move 5s | move 30s | post |
|---|---|---|---|---|---|---|
| 13.0 | NVDA | +0 | -1.0 | +3.0 | +11.0 | Retail investors keep talking about NVDA on forums |
| 82.4 | CRWV | +2 | +18.0 | +18.5 | +8.5 | Analyst upgrades CRWV to Strong Buy, sees 30% upside |
| 121.7 | AMD | +2 | +0.0 | +25.5 | +32.0 | AMD smashes earnings expectations, raises full-year guidance |
| 207.0 | MU | -2 | -13.0 | -14.0 | -21.0 | Short seller publishes report questioning MU accounting |
| 252.9 | VRT | -2 | -10.5 | -9.5 | -11.5 | VRT misses revenue estimates, shares slide after hours |
| 337.9 | NVDA | +1 | +1.0 | +19.0 | +6.5 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 337.9 | AMD | +1 | +1.5 | +2.5 | -10.0 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 337.9 | AVGO | +1 | +1.5 | +4.5 | +5.5 | NVDA unveils next-gen chip, analysts call it a breakthrough |
| 426.7 | NBIS | -1 | +0.0 | -8.0 | -9.0 | Export restrictions could hit NBIS sales, sources say |
| 511.5 | NBIS | +2 | -0.5 | +15.5 | +15.5 | NBIS smashes earnings expectations, raises full-year guidance |
| 592.1 | NVDA | +0 | +0.5 | -6.0 | -6.0 | NVDA CEO spotted at coffee shop, says 'busy times' |

- 1s after a post with a clear sentiment, price moved **+5.00 ticks** in the direction of the words on average (n=9, 67% of the time the right way)
- 5s after a post with a clear sentiment, price moved **+13.00 ticks** in the direction of the words on average (n=9, 100% of the time the right way)
- 30s after a post with a clear sentiment, price moved **+11.06 ticks** in the direction of the words on average (n=9, 89% of the time the right way)

Rule of thumb: switch news trading on (news_trade_size 20-50) only if the 5s number is clearly bigger than half the spread and right more than ~65% of the time.

## Simulator calibration (copy into optisim/scenarios.py)

Stocks: name: (price, maker half-spread in ticks, top-of-book size, trades/min). Compare with BONA_FIDE.

- AMD: (165.47, 0.62, 600, 90.1)
- AVGO: (209.05, 0.65, 411, 170.1)
- CRWV: (144.14, 0.63, 68, 116.5)
- MU: (77.91, 0.61, 944, 26.3)
- NBIS: (94.50, 0.62, 74, 58.0)
- NVDA: (127.69, 0.61, 517, 59.4)
- SNDK: (53.99, 0.59, 95, 27.6)
- VRT: (64.26, 0.94, 2808, 15.7)
