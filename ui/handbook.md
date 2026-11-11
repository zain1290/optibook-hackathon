# Handbook {#top}

This handbook explains the control panel from zero. You do not need any trading or programming background. Words in the [Glossary](#glossary) are explained the first time you would meet them, and every setting in the panel has a **?** button that jumps to its explanation here.

## Start here {#start}

The panel controls a trading bot: a small program that buys and sells on an exchange by itself. You tell it what to do, watch how it is doing, and change its settings while it runs. You never have to type commands.

The panel has five tabs:

- **Run**: choose what to do (watch the market, trade, practise, or close everything) and start it.
- **Monitor**: live charts and numbers while the bot runs, plus the switches to change it.
- **Past runs**: every run is saved. Open its report, its charts, or download it as a zip file.
- **Backtest**: try settings on practice markets before using them for real.
- **Handbook**: this page.

The coloured bar at the top is always visible. **Grey** means nothing is running. **Blue** means watching or practising, so no real money is at risk. **Red stripes** mean the bot is trading on the real exchange. The Stop and Flatten buttons live in that bar so you can always reach them.

**One rule before anything else:** the exchange allows [one connection per team](#g-one-connection). If the bot runs, nobody else in the team may connect with the team login (no second bot, no notebook). Teammates watch the exchange's own web visualizer instead.

## The market in plain words {#market}

An [exchange](#g-exchange) is a marketplace where people send [orders](#g-order) to buy or sell. The thing being traded (here a company's share) is called an [instrument](#g-instrument). Quantities are counted in [lots](#g-lot); one lot is one share here.

Every instrument has an [order book](#g-order-book): a list of everyone waiting to buy, and everyone waiting to sell, with their prices.

| Waiting to buy (bids) | Price | Waiting to sell (asks) |
|---|---|---|
| | 163.3 | 1000 lots |
| | 163.2 | 2000 lots |
| | 163.1 | 3000 lots |
| 3000 lots | 162.7 | |
| 2000 lots | 162.6 | |
| 1000 lots | 162.5 | |

This is roughly what AMD looked like on the practice exchange. The highest buying price (162.7) is the [best bid](#g-bid); the lowest selling price (163.1) is the [best ask](#g-ask). The gap between them is the [spread](#g-spread), here 0.4. Prices move in fixed steps called [ticks](#g-tick); with a tick of 0.1, that spread is 4 ticks. The middle of the best bid and best ask (162.9) is the [mid price](#g-mid), a good guess of what the share is really worth, its [fair value](#g-fair-value).

A trade happens when a buyer and a seller agree on a price. If you send a buy order at 163.1 or higher, you trade immediately with the seller at 163.1: you were the [aggressive](#g-aggressive) side and you [crossed the spread](#g-cross). If you send a buy at 162.8, nobody is selling that cheap, so your order waits in the book: you are [passive](#g-passive), and you trade only when someone sells to you. Orders at the same price wait in a [queue](#g-queue): first come, first served.

What you hold is your [position](#g-position). Bought 10 = long 10 (+10). Sold 10 you did not own = short 10 (-10). [PnL](#g-pnl) (profit and loss) is how much money you have made or lost, counting what your current position is worth. On Optibook, open positions are valued at the [last traded price](#g-ltp).

## This challenge: what the practice exchange shows {#challenge}

What we saw on the Bona Fide Optibook site the evening before (the real round may differ; the brief decides):

- **Eight stocks**, all AI and chip companies: AMD, AVGO, NVDA (chips), MU, SNDK (memory), CRWV, NBIS (AI cloud), VRT (data-centre power). Companies in the same [sector](#g-sector) tend to move together.
- **One big exchange [market maker](#g-market-maker) per stock** quotes 1000 to 3000 lots on each side, 2 to 13 ticks wide depending on the stock. It is a computer program run by the exchange.
- **[Background traders](#g-bots)** buy or sell 20 lots at a time at the best price, about once every 5 seconds per stock.
- A **[news feed](#g-news)**: the exchange can publish social media posts about the companies, which may move prices.
- The leaderboard shows PnL, [delta](#g-delta), [cash delta](#g-cash-delta), position, [vega](#g-vega) and an [hourly Sharpe](#g-sharpe). Vega only matters if [options](#g-option) are listed; the exchange's software supports options, [futures](#g-future) and [ETFs](#g-etf), so the bot is ready for them.
- Rules from the FAQ: [one connection per team](#g-one-connection), [cancel on disconnect](#g-cancel-on-disconnect), a [position limit](#g-position-limit) per instrument (their example: 300), and no notification when an order trades (the bot checks itself).

### If the brief is a dual listing instead {#dual}

Optibook challenges are often a [dual listing](#g-dual-listing): one company listed on two markets, one **busy** ([liquid](#g-liquidity)) and one **thin**. Because they are the same company, both should be worth the same. The 'Dual listing' strategy (evolved) is built for that case: it quotes on the thin listing and [hedges](#g-hedge) every trade on the busy one, keeping the [net delta](#g-net-delta) near 0. Use it only if the brief names two listings of one company (for example ASML and ASML_DUAL).

## How the bot makes money {#money}

The recommended bot ('Everything', code name combo) combines four ideas.

**1. Quoting just inside the exchange maker.** The exchange maker's quotes are centred on fair value, a few ticks wide. The bot places its own [quotes](#g-quote) 1 tick better, but always at least 'Distance from fair value' away from fair value. The background traders' 20-lot orders then trade with us first, and we earn the gap between our price and fair value. When we hold a position, the bot [skews](#g-skew) its quotes so the position shrinks again.

**2. Picking off mistakes.** Other teams leave quotes behind after a price move ([stale quotes](#g-stale)), or dump positions below fair value. The bot [picks those off](#g-pick-off): it buys anything offered 1 tick or more under fair value and sells into anything bid 1 tick or more over it. In the simulator this earned more than everything else together.

**3. Stepping aside on news.** When a post names a stock (or its sector), the bot pulls its quotes on that stock for a few seconds, so nobody can trade against us at old prices. Optionally it also trades in the direction of the news.

**4. Derivatives, if listed.** It prices options, futures and ETFs from the stocks they depend on, trades them when the market price is off, and hedges the resulting stock exposure.

Worked example: AMD's maker shows 162.7 bid / 163.1 ask, so fair value is about 162.9. The bot bids 162.8 and asks 163.0 (1 tick inside, 1 tick from fair value; the default keeps 1.5 ticks, so it would sit at 162.7 / 163.1 here and join the queue instead). A background trader sells 20 lots: they hit our 162.8 bid first. We are long 20, bought 0.1 under fair value, a profit of about 2.0 if we sell again near fair value. Our quotes now lean lower to sell those 20.

**Why fair value is the 'deep' mid:** small orders from other teams inside the spread can be moved at will. The bot ignores them and takes the middle of where real size (200 lots or more) sits. In the simulator, a fair value that listened to small orders lost money.

## Using the panel {#panel}

### The status bar {#bar}

Shows what is running, how long, and the key numbers: PnL, net delta, positions, orders per second, and rejected orders (should be 0).

| Button | What it does | Positions after |
|---|---|---|
| Pause trading | Pulls our quotes and stops trading. Press again to resume. | Unchanged |
| Stop | Ends the run cleanly, applying your 'When stopping' choice. | Depends on that choice |
| Flatten and stop | Closes every position at market prices, then stops. Asks you to click twice. | All zero |

### Run tab {#tab-run}

Four steps, top to bottom.

1. **What do you want to do?** Observe (watch the real market, no orders), Trade live (real orders), Rehearse (the same thing on a simulated practice market), or Flatten now (close everything).
2. **Strategy.** 'Everything' is the recommended bot. 'Stocks only' and 'Options, futures, ETFs only' are its two halves. The dual listing strategies are for the case above. Presets fill in tried settings: 'First live minutes' (small, careful), 'Recommended', 'News trader', 'Cautious', 'Dual listing'.
3. **Settings.** Grouped by purpose. Every setting shows its plain name, its code name in small print, a one-line explanation, and a **?** for the full story. Blue labels mark values you changed. The essentials are open; rarer ones are under 'Advanced'.
4. **Start.** The box on the right says in one sentence what will happen. Live trading and Flatten ask for a second click. 'Show command' shows the exact command.

Observe, Trade live and Flatten now only work where the exchange's Optibook client is installed (Optiver's Dev Environment). Rehearse works everywhere. The panel refuses to start a second live connection while another program holds it.

### Monitor tab {#tab-monitor}

- **What to do now**: plain-language advice worked out from the latest numbers. Green means nothing needs attention.
- **PnL** chart: profit over time.
- **Positions** chart: what we hold; with many stocks, the 4 with the biggest positions.
- **Prices and our trades**: with several stocks, the % change since the start of the 4 we trade most, with a ▲ for each of our buys and a ▼ for each sell.
- **Market and our quotes**: per stock the spread, mid, our position, our current quotes, how much rivals offer at our price or better, and how many trades happened.
- **Where the money comes from**: every trade grouped by why it happened. 'Edge at trade' is what the trade was worth against fair value at that moment; 'After 1 s / 5 s / 30 s' is the same measured later (the [markout](#g-markout)). Positive and green is good. Rows: 'Picked off a wrong quote' (take), 'Our waiting quote was hit' (quote), 'Traded on news' (news), derivative rows, and closing trades.
- **Live settings**: change any setting while the bot runs. Edit, then press 'Apply changes'; the bot picks it up within about a second.
- **Health**: orders per second, [rejected](#g-reject) and [throttled](#g-throttle) orders, loop times, our [hourly Sharpe](#g-sharpe) estimate, [cash delta](#g-cash-delta) and how many news posts arrived.
- **News**: the posts the exchange published, newest first.
- **Events**: settings changes, pauses, errors and lost connections, newest first.
- **Notes**: write what you see (leaderboard, the brief, what you changed and why). Saved with the run.

### Past runs tab {#tab-runs}

Every run is saved in its own folder with everything the bot saw and did. Click a run for its summary and full report. 'Analyze' writes the report (including a news impact table and simulator calibration numbers), 'Open in Monitor' shows its charts, 'Download zip' packs it up to share.

### Backtest tab {#tab-backtest}

Tries strategies or tweaks on practice markets the strategy was never tuned on ([held-out markets](#g-held-out)). Write variants separated by spaces: `combo` is a strategy with its defaults; `stock_mm:take_edge=2` changes one setting; `combo:size=10,quote_edge=2` changes two; `v8` is a version of the dual listing strategy. Results show average PnL, average rank among 13 teams, how often it finished first, PnL compared with the best rival, the biggest net delta, and the hourly Sharpe.

## Settings, explained one by one {#settings}

{{PARAMS}}

## Strategies and versions {#strategies}

| Strategy | Code name | Use it when |
|---|---|---|
| Everything (recommended) | combo | Default. Stocks, and derivatives if listed, on one connection. |
| Stocks only | stock_mm | First careful live minutes, or if derivatives misbehave. |
| Options, futures, ETFs only | deriv_arb | Testing the derivative part alone. |
| Pairs trading | pairs | Only after tools/pair_stats.py shows a pair worth it. |
| Dual listing | evolved | The brief is one company on two listings. |
| Dual listing, safe start | cross_arb | First minutes of a dual listing challenge. |

What the simulator said (10-minute practice markets, 6 different markets each, 12 rival teams; PnL in the market's currency):

| Practice market | Stocks only | + news trading | No picking off |
|---|---|---|---|
| bonafide (standard) | +1,962, 1st in 3 of 6 | +2,297 | about 0 |
| bonafide_quiet (today's market, no rivals) | +1,615 | +2,248 | +1,615 |
| bonafide_informed | +2,019 | +2,227 | -274 |
| bonafide_clones (half the rivals copy us) | +846 | +972 | -25 |

Read it as: picking off is the big earner whenever there are rivals; news trading helps if news really moves prices (in the simulator it was built to); copies of our own bot are the toughest rivals. On the derivatives market, 'Everything' added about +7,000 on top, but the simulated derivative maker is easy to beat, so treat that as a check that the pricing works, not a forecast.

The dual listing strategy 'evolved' grew through numbered versions:

| Version | What it added, in plain words |
|---|---|
| v0 | Identical to quote_hedge. |
| v1 | Hedge with a waiting order in the middle of the busy listing's spread instead of paying to cross it. |
| v2 | Leave quotes alone when they are close enough (saves orders, keeps our place in line); arbitrage only the thin side. |
| v3 | Price quotes from fair value and the real cost of hedging, so we can quote as tightly as our costs allow. |
| v4 | Stop leaning quotes on positions that are already hedged (it was costing trades). |
| v5 | Try hedging at the best price first. Test only: its gain came from a quirk of the simulator. |
| v6 | Same as v5, but measured live: the bot only uses it where it actually works. |
| v7 | Same logic as v6; the stopping rule changed to close only uncovered risk. |
| v8 | Arbitrage counts hedging cost, which fixed losses in markets with a 1-tick spread. **Safest all-round.** |
| v9 | Same logic as v8; the lesson was to run the loop faster. |
| v10 | Quote size 15. **Better when the busy spread is 2+ ticks, worse when it is 1 tick.** |

## Practice markets {#markets}

| Market | What is different | Use it to |
|---|---|---|
| bonafide | The 8 practice stocks with their real spreads and sizes, background traders, news, and 12 rival teams (market makers, naive bots, news chasers). The standard. | Practise and compare. |
| bonafide_quiet | The same market with no rivals: what the practice exchange looked like the evening before. | Check the bot works at all. |
| bonafide_clones | Half the rivals run a copy of our bot. | See what happens when everyone has the same idea. |
| bonafide_informed | A third of background trades know where prices go; the exchange maker is slower. | Check we are not easy prey. |
| bonafide_leadlag | The thin stocks' maker reacts late to sector moves. | Test pairs trading. |
| bonafide_derivs | Adds an ETF on the chip stocks, NVDA options and an NVDA future. | Test the derivatives part. |
| crowded and others | Dual listing markets (one company, two listings). | Only if the brief is a dual listing. |

The simulated rivals and exchange traders are educated guesses, not the real thing. Use practice results to compare settings, not to predict real profit.

## A plan for the day {#plan}

1. Read the brief. Paste the position limit, the order rate limit, the instruments and how scoring works into the run's Notes.
2. Get the code into the Dev Environment (docs/DEPLOY.md, about 5 minutes) and stop every other connection.
3. Run `tools/intro_exercises.py`: it trades 1 lot, checks every call the bot uses, and prints the error texts and latency.
4. Run **Observe** for 5 minutes. Analyze it: spreads, sizes, news impact, and which instruments exist.
5. Set **Position limit** and **Order budget** from the brief (stay a little under the real rate limit).
6. Start **Trade live** with the preset 'First live minutes'. Confirm in the Monitor that quotes rest, trades happen and nothing is rejected.
7. Switch to 'Recommended'. Watch 'What to do now' and the money table; change settings live. Write every change and the reason in Notes.
8. If news moves prices (news impact report), try 'Trade on news' 20 to 50.
9. A few minutes before the end, set 'end_in_secs' (or use 'Stop after') so the bot winds down, then Flatten and stop if the brief wants you flat.

## If you see this, do that {#playbook}

| What you see | What it means | What to do |
|---|---|---|
| 'Our waiting quote was hit' negative after 5 s | Prices move against us right after we trade: faster traders or news pick off our quotes. | Raise Distance from fair value (quote_edge) to 2, or lower Quote size. |
| 'Picked off a wrong quote' negative after 5 s | What looked like a mistake was a real price move. | Raise Pick-off threshold (take_edge) to 2, or 0 to switch off. |
| 'Traded on news' negative | Prices do not follow the words. | Trade on news back to 0. |
| Rejected orders > 0 | The exchange refused orders. The Health box and Events show why. | Position limit: lower Quote size or Soft limit. Rate limit: lower Order budget. Price band: report it. |
| Held back (throttled) is high | The bot wanted to send more orders than its budget. | Set 'Only the widest stocks' to 4, or raise 'Keep quotes in place'. |
| Positions near the limit | The bot cannot add more on that side. | Raise Inventory lean (skew_per_lot) or lower Pick-off size. |
| 'Connection lost' in Events | Someone else connected with the team login. | Find and stop the other program or notebook. |
| No quote trades for minutes | Rivals offer better prices, or the market is quiet. | Look at 'Rivals at our price or better'. Do not chase by dropping quote_edge below 1. |
| Busy spread is 1 tick (dual listing) | Hedging always costs half a tick. | Use v8 with Quote size 10. |
| Anything strange | | Pause trading, look, then decide. |

## Troubleshooting {#trouble}

- **Observe, Trade live and Flatten now are greyed out.** The Optibook client is not installed on this computer. Run the panel in the Dev Environment. Rehearse still works.
- **'Another program holds the team's exchange connection'.** A bot started from a terminal is still running. Stop it there (Ctrl+C), then start from the panel.
- **The status bar says the panel server is not reachable.** The program behind the panel stopped. Start it again: `python ui/server.py`.
- **The Monitor shows no numbers yet.** The first summary arrives about 10 seconds after starting.
- **Errors in Events.** One bad response does not stop the bot. If errors repeat, Pause, download the run's zip from Past runs, and ask for help.
- **The dual listing strategy finds no pairs.** The exchange has no dual listing; use 'Everything'.
- **The bot feels slow.** Health shows the loop and recorder times. Raise 'Record every N loops' to 2 or 3.

## Glossary {#glossary}

### Adverse selection {#g-adverse}
Trading mostly with people who know more than you, so prices tend to move against you after you trade. Shows up as negative markouts.

### Aggressive {#g-aggressive}
An order that trades immediately by accepting someone else's waiting price. Fast but pays the spread. Opposite of passive.

### Arbitrage {#g-arbitrage}
Buying something where it is cheap and selling the same thing where it is expensive at the same time, keeping the difference with little risk.

### Ask {#g-ask}
A price at which someone is waiting to sell. The best ask is the lowest one.

### Background traders {#g-bots}

Computer programs run by the exchange that buy or sell now and then (on the practice exchange: 20 lots at a time). Market makers earn the spread from them.

### Backtest {#g-backtest}
Running a strategy on practice markets to see how it would have done.

### Bid {#g-bid}
A price at which someone is waiting to buy. The best bid is the highest one.

### Cancel on disconnect {#g-cancel-on-disconnect}

When a program's connection to the exchange ends (it stops, crashes, or is kicked off), the exchange cancels all its waiting orders. Positions stay. The bot reconnects and quotes again by itself.

### Cash delta {#g-cash-delta}

Total money value of what you hold: each position times its price, added up (shorts count negative). Shows how much a 1% market move would roughly change PnL (1% of cash delta).

### Cross the spread {#g-cross}
Buying at the best ask or selling at the best bid, so you trade immediately. Costs about half the spread compared with the mid price.

### Crossed (listings) {#g-crossed}
When one listing's best bid is higher than the other listing's best ask, so you could buy on one and sell on the other at a profit. The Monitor shows how often this happens.

### Delta {#g-delta}

How much a position's value changes when a stock moves by 1. For a share it is the number of shares; for an [option](#g-option) it is between 0 and 1 (calls) or -1 and 0 (puts) per option. Adding the delta of everything you hold in one stock tells you your real exposure to it.

### Dual listing {#g-dual-listing}
The same company traded on two markets. Here: the busy primary listing and the thin dual listing.

### Edge {#g-edge}
How much a trade is worth compared with fair value, in ticks. Buying below fair value or selling above it is positive edge.

### ETF {#g-etf}

Exchange traded fund: one instrument that tracks a basket of others (for example the chip stocks). Its fair value follows from the basket's prices, so a mispriced ETF can be traded against the basket.

### Exchange {#g-exchange}
The marketplace that matches buyers and sellers. In the challenge: Optiver's practice exchange, Optibook.

### Expired {#g-expired}

An option or future past its end date. It can no longer be traded and settles at its final value.

### Fair value {#g-fair-value}
What an instrument is really worth. The bot uses the busy listing's mid price as its best estimate.

### Fill {#g-fill}
A trade that happened to one of our orders. A partial fill trades only part of the order.

### Flatten {#g-flatten}
Closing every position so you hold nothing and have no risk.

### Future {#g-future}

An agreement to buy a stock at a set price on a later date. Its fair value is about the stock price plus interest until that date.

### Greeks {#g-greeks}

How an option's price reacts to changes: delta (stock price), gamma (how delta changes), vega (volatility), theta (time passing), rho (interest rates).

### Hedge {#g-hedge}
A second trade that cancels out the price risk of the first. Here: the opposite trade on the other listing.

### Held-out markets {#g-held-out}
Practice markets never used to tune the strategy. Testing on them shows whether an improvement is real or only fits the markets it was tuned on.

### Hourly Sharpe {#g-sharpe}

Profit per unit of risk: the average PnL gain per period divided by how much it swings, scaled to an hour. Steady small gains score higher than wild swings with the same total. The leaderboard shows it; the panel shows our own estimate.

### Instrument {#g-instrument}
Anything that can be traded. Each listing (ASML, ASML_DUAL) is its own instrument.

### Inventory {#g-inventory}
Another word for position: what we currently hold.

### IOC order {#g-ioc}
'Immediate or cancel': trades whatever it can right now and cancels the rest. Never waits in the book. Used for urgent hedges.

### Last traded price {#g-ltp}

The price of the most recent trade in an instrument. Optibook values open positions at it, so one late trade at an odd price can move your PnL. Ending flat avoids that.

### Latency {#g-latency}
How long something takes, for example how long the exchange takes to answer an order. Lower is better.

### Limit order {#g-limit-order}
An order with a price limit that waits in the book until someone trades with it or it is cancelled.

### Liquidity {#g-liquidity}
How easy it is to trade without moving the price. A liquid listing has many traders and a tight spread.

### Loop {#g-loop}
One cycle of the bot: look at the market, decide, send orders. It repeats every 'Loop period' seconds.

### Lot {#g-lot}
The unit of quantity. Here one lot is one share.

### Market maker {#g-market-maker}
A trader who always offers to both buy and sell, earning the gap between the two prices.

### Markout {#g-markout}
How much a trade turned out to be worth some seconds later, measured against the fair value at that time. Positive means the price moved our way. Consistently negative means we are being picked off.

### Mid price {#g-mid}
Halfway between the best bid and best ask.

### Net delta {#g-net-delta}
The risk left after hedging: position on the busy listing plus position on the thin listing. Long 30 on one and short 30 on the other gives net delta 0.

### News feed {#g-news}

Social media posts the exchange publishes during the round. The bot reads which companies a post names and whether the words are good or bad ([sentiment](#g-sentiment)).

### One connection per team {#g-one-connection}

The exchange lets each team have one live connection. A second one (another bot, a notebook) kicks the first off, and then the exchange cancels all its orders.

### Option {#g-option}

The right, not the duty, to buy (a call) or sell (a put) a stock at a set price (the strike) until a set date (the expiry). Its value depends on the stock price, time left and [volatility](#g-volatility); the bot uses the Black-Scholes formula.

### Order book {#g-order-book}
The list of all waiting buy and sell orders for an instrument, sorted by price.

### Order {#g-order}
An instruction to buy or sell a number of lots at a price.

### Pairs trading {#g-pairs}

Betting that the gap between two related stocks returns to normal: sell the one that got expensive, buy the cheap one. Pays only if the gap swings by more than the cost of crossing both spreads.

### Passive {#g-passive}
An order that waits in the book for someone else to trade with it. Earns the spread instead of paying it, but may not get filled.

### Pause (instrument) {#g-pause}
The exchange can halt trading in an instrument. The bot pulls its quotes there and hedges elsewhere if needed.

### Pick off {#g-pick-off}

To trade straight away against someone's quote that is now wrong (stale after a move, or priced below fair value). Good for the one who picks off, costly for the one picked off.

### PnL {#g-pnl}
Profit and loss: money made or lost, including what current positions are worth.

### Position limit {#g-position-limit}
The largest position the rules allow. The exchange refuses orders that could break it.

### Position {#g-position}
What you hold. Positive (long) means you own it; negative (short) means you sold more than you owned.

### Price band {#g-price-band}

Exchanges often refuse orders priced too far from the last trade (Optibook calls it a price change limit). The intro exercises script shows the exact rule.

### Queue {#g-queue}
Orders waiting at the same price, in arrival order. The first in line trades first. Cancelling and re-sending moves you to the back.

### Quote {#g-quote}
Our own waiting buy order and sell order.

### Rate limit {#g-rate-limit}
The most orders per second the exchange accepts from one team.

### Rehearsal {#g-rehearsal}
A run on the simulated practice market, at real speed if you want, with the same screens as live trading.

### Reject {#g-reject}
An order the exchange refused, for example because it could break the position limit or the rate limit.

### Sector {#g-sector}

A group of companies in the same business (chips, memory, cloud). News or moods often move a whole sector together.

### Seed {#g-seed}
A number that decides which random practice market you get. Same seed, same market.

### Self-trade {#g-self-trade}
When our own buy order would trade with our own sell order. The exchange blocks it.

### Sentiment {#g-sentiment}

Whether a news post is good or bad for a company. The bot counts good words (beats, upgrade, record) and bad words (misses, probe, resigns).

### Skew {#g-skew}
Shifting both quotes up or down to make the trades we want more likely, for example to reduce a large position.

### Spread {#g-spread}
The gap between the best ask and the best bid. Narrow spread means a busy, cheap-to-trade market.

### Stale quote {#g-stale}

A waiting order whose price was fine a moment ago but is wrong now because the market moved. Stale quotes get [picked off](#g-pick-off).

### Throttle {#g-throttle}
When the bot holds back an order because it reached its own order budget for that second. Protects us from the exchange's rate limit.

### Tick {#g-tick}
The smallest price step. With a tick of 0.1, prices are 100.0, 100.1, 100.2 and so on.

### Vega {#g-vega}

How much an option position gains or loses when volatility rises by one point. Only matters if options are traded.

### Version {#g-version}
A saved stage of the evolved strategy (v0 to v10). Each one added a single tested improvement.

### Volatility {#g-volatility}

How much a price moves around, as a yearly percentage (0.3 = 30%). Higher volatility makes options more valuable.

### Z-score {#g-z-score}

How unusual a number is: how many standard deviations it is from its recent average. 2.5 means quite unusual.
