# Run report: 20261112-135647_combo_sim

- Mode: **sim** (scenario bonafide, teams 12, seed 2)
- Strategy: **combo**, params {}, loop 0.1s
- Duration: 10.0 min, loops 6000, stop: time limit, errors: 0
- Final PnL: **1090.00**, max drawdown 30.50, final positions {'AMD': 0, 'AVGO': 0, 'NVDA': 0, 'MU': 0, 'SNDK': 0, 'CRWV': 0, 'NBIS': 0, 'VRT': 0}
- Hourly Sharpe (our estimate of the leaderboard number): **17.94**, reconnects: 0, news posts: 10
- Code: d802ce1 dirty=False, optibook None

## Leaderboard (sim): we are **4/13**

| rank | team | pnl (fair) | pnl (last price) | hourly sharpe | volume |
|---|---|---|---|---|---|
| 1 | team03_mm | 1578.92 | 1519.00 | 11.31 | 12410 |
| 2 | team04_mm | 1373.04 | 1334.50 | 19.27 | 13600 |
| 3 | team07_mm | 1258.95 | 1249.00 | 28.38 | 15580 |
| 4 | us | 1090.00 | 1090.00 | 18.45 | 12350 |
| 5 | team02_news | 95.00 | 95.00 | 2.93 | 600 |
| 6 | team11_mm | -10.96 | -15.00 | -0.92 | 785 |
| 7 | team05_news | -23.50 | -23.50 | -3.48 | 540 |
| 8 | team01_mm | -134.74 | -221.50 | -1.75 | 18615 |
| 9 | team06_mm | -250.98 | -255.00 | -9.89 | 3935 |
| 10 | team09_mm | -251.35 | -239.00 | -3.56 | 1380 |
| 11 | team08_mm | -950.88 | -973.50 | -6.67 | 12135 |
| 12 | team00_naive | -1707.50 | -1638.50 | -6.25 | 13580 |
| 13 | team10_naive | -2918.23 | -2883.00 | -5.45 | 36275 |

## Market

| instrument | tick | spread (ticks, time-wtd) | top size | % time two-sided | trades/min | volume/min | mid change sd (ticks/update) |
|---|---|---|---|---|---|---|---|
| AMD | 0.10 | 1.80 | 719.34 | 99.97 | 103.51 | 1587.68 | 0.76 |
| AVGO | 0.10 | 1.75 | 435.33 | 99.97 | 123.60 | 1903.41 | 0.82 |
| CRWV | 0.10 | 1.84 | 41.03 | 99.97 | 97.42 | 1545.21 | 0.77 |
| MU | 0.10 | 1.46 | 1122.17 | 99.97 | 23.98 | 513.57 | 0.63 |
| NBIS | 0.10 | 1.59 | 43.82 | 99.97 | 65.85 | 1140.05 | 0.60 |
| NVDA | 0.10 | 1.70 | 624.75 | 99.97 | 67.24 | 1073.61 | 0.62 |
| SNDK | 0.10 | 1.36 | 73.33 | 99.97 | 29.38 | 573.52 | 0.60 |
| VRT | 0.10 | 1.85 | 2767.94 | 99.97 | 15.69 | 249.29 | 0.59 |

### Counterparties (17 distinct names seen in public trades)

| instrument | name | volume | of which aggressive | share of instrument volume % |
|---|---|---|---|---|
| NBIS | team10_naive | 7940 | 895 | 34.79 |
| AMD | team10_naive | 6730 | 585 | 21.18 |
| CRWV | team10_naive | 6485 | 195 | 20.97 |
| AVGO | team01_mm | 5725 | 590 | 15.03 |
| NVDA | team10_naive | 5640 | 290 | 26.24 |
| AVGO | team08_mm | 4560 | 0 | 11.97 |
| AVGO | team07_mm | 4420 | 3685 | 11.60 |
| AVGO | team04_mm | 3960 | 3890 | 10.39 |
| CRWV | team07_mm | 3900 | 3285 | 12.61 |
| AVGO | team10_naive | 3850 | 0 | 10.10 |
| AMD | team01_mm | 3725 | 1965 | 11.72 |
| AVGO | us | 3650 | 3610 | 9.58 |
| SNDK | team10_naive | 3450 | 600 | 30.05 |
| CRWV | us | 3240 | 3200 | 10.48 |
| CRWV | team01_mm | 3225 | 745 | 10.43 |
| AVGO | team03_mm | 3205 | 3025 | 8.41 |
| CRWV | team04_mm | 3185 | 3145 | 10.30 |
| CRWV | team03_mm | 3130 | 2920 | 10.12 |
| AMD | GroovyGrapefruits | 2895 | 1970 | 9.11 |
| AMD | team07_mm | 2785 | 2250 | 8.76 |
| AMD | team00_naive | 2730 | 295 | 8.59 |
| CRWV | team00_naive | 2700 | 0 | 8.73 |
| MU | GroovyGrapefruits | 2650 | 2160 | 25.78 |
| MU | JazzyJellies | 2580 | 2580 | 25.10 |
| SNDK | LivelyLasagnas | 2570 | 2570 | 22.39 |

## Our orders

| action | tag | count | per min |
|---|---|---|---|
| insert_order | quote | 3793 | 378.98 |
| delete_order | cancel_stale | 2957 | 295.45 |
| delete_order | requote | 799 | 79.83 |
| insert_order | take | 724 | 72.34 |
| amend_order | resize | 87 | 8.69 |
| delete_orders | news_pull | 11 | 1.10 |
| delete_orders | - | 8 | 0.80 |
| insert_order | flatten | 7 | 0.70 |

| action | latency p50 ms | p95 ms | max ms |
|---|---|---|---|
| insert_order | 0.03 | 0.05 | 0.45 |
| delete_order | 0.01 | 0.01 | 0.07 |
| delete_orders | 0.01 | 0.01 | 0.04 |
| amend_order | 0.01 | 0.01 | 0.05 |

Peak ops in any 1 s window: **25**, average 13.97/s, client-side throttled: 32453

## Fills: where the money came from

Edge = (fair mid - price) for buys, (price - fair mid) for sells, in ticks; fair mid = primary listing mid (dual listing) or the deep mid, where at least 200 lots sit on each side (stocks). Markout = same thing measured h seconds later. Positive = good for us.

| tag | fills | volume | edge at fill (ticks/lot) | markout 1s | markout 5s | markout 30s | edge x volume (currency) |
|---|---|---|---|---|---|---|---|
| take | 792 | 12000 | 1.12 | 0.83 | 1.04 | 0.97 | 1343.00 |
| quote | 17 | 205 | 0.24 | 0.59 | 0.55 | -4.36 | 5.00 |
| flatten | 11 | 145 | -2.33 | - | - | - | -33.75 |

By instrument (edge x volume at the moment of the fill, in currency):

| instrument | volume | edge x volume |
|---|---|---|
| AVGO | 3650 | 434.50 |
| CRWV | 3240 | 366.75 |
| NBIS | 1740 | 196.50 |
| AMD | 1810 | 161.00 |
| NVDA | 1350 | 104.50 |
| SNDK | 540 | 53.00 |
| VRT | 20 | -2.00 |

Time from order sent to fill: p50 0.10 s, p95 0.20 s

## Risk

| instrument | max abs position |
|---|---|
| AMD | 20 |
| AVGO | 45 |
| CRWV | 55 |
| MU | 0 |
| NBIS | 60 |
| NVDA | 20 |
| SNDK | 40 |
| VRT | 10 |

| pair | max abs net delta | % time net delta not 0 |
|---|---|---|

## News impact (11 post x instrument pairs)

| t (s) | instrument | sentiment | move 1s | move 5s | move 30s | post |
|---|---|---|---|---|---|---|
| 11.3 | MU | +2 | +11.5 | +12.5 | +11.5 | AI spending boom continues: memory names rally |
| 11.3 | SNDK | +2 | +6.0 | +7.0 | +7.0 | AI spending boom continues: memory names rally |
| 46.3 | MU | -2 | -8.5 | -10.0 | -8.5 | MU misses revenue estimates, shares slide after hours |
| 94.9 | AMD | +0 | -0.5 | -4.0 | -2.0 | Retail investors keep talking about AMD on forums |
| 138.8 | AMD | +1 | +1.0 | +12.0 | +23.5 | Reports: hyperscaler signs multi-billion order with AMD |
| 205.1 | NBIS | -2 | -0.5 | -7.0 | -4.5 | Short seller publishes report questioning NBIS accounting |
| 294.9 | MU | +0 | +0.0 | +0.5 | +7.0 | MU to present at industry conference next week |
| 345.7 | NVDA | +0 | -1.0 | -3.0 | -17.0 | NVDA CEO spotted at coffee shop, says 'busy times' |
| 417.3 | VRT | +2 | -0.5 | +5.5 | +8.5 | AI spending boom continues: power names rally |
| 499.6 | CRWV | +0 | -3.0 | -2.5 | -17.5 | CRWV CEO spotted at coffee shop, says 'busy times' |
| 549.8 | VRT | +0 | +0.0 | +2.0 | +0.0 | Retail investors keep talking about VRT on forums |

- 1s after a post with a clear sentiment, price moved **+4.50 ticks** in the direction of the words on average (n=6, 83% of the time the right way)
- 5s after a post with a clear sentiment, price moved **+9.00 ticks** in the direction of the words on average (n=6, 100% of the time the right way)
- 30s after a post with a clear sentiment, price moved **+10.58 ticks** in the direction of the words on average (n=6, 100% of the time the right way)

Rule of thumb: switch news trading on (news_trade_size 20-50) only if the 5s number is clearly bigger than half the spread and right more than ~65% of the time.

## Simulator calibration (copy into optisim/scenarios.py)

Stocks: name: (price, maker half-spread in ticks, top-of-book size, trades/min). Compare with BONA_FIDE.

- AMD: (163.03, 0.90, 719, 103.5)
- AVGO: (209.38, 0.87, 435, 123.6)
- CRWV: (141.48, 0.92, 41, 97.4)
- MU: (78.84, 0.73, 1122, 24.0)
- NBIS: (92.08, 0.80, 44, 65.8)
- NVDA: (122.55, 0.85, 625, 67.2)
- SNDK: (53.51, 0.68, 73, 29.4)
- VRT: (64.97, 0.92, 2768, 15.7)
