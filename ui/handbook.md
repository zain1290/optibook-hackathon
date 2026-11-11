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

## The market in plain words {#market}

An [exchange](#g-exchange) is a marketplace where people send [orders](#g-order) to buy or sell. The thing being traded (here a company's share) is called an [instrument](#g-instrument). Quantities are counted in [lots](#g-lot); one lot is one share here.

Every instrument has an [order book](#g-order-book): a list of everyone waiting to buy, and everyone waiting to sell, with their prices.

| Waiting to buy (bids) | Price | Waiting to sell (asks) |
|---|---|---|
| | 100.3 | 25 lots |
| | 100.2 | 40 lots |
| 30 lots | 100.0 | |
| 15 lots | 99.9 | |

The highest buying price (100.0) is the [best bid](#g-bid); the lowest selling price (100.2) is the [best ask](#g-ask). The gap between them is the [spread](#g-spread), here 0.2. Prices move in fixed steps called [ticks](#g-tick); with a tick of 0.1, the spread above is 2 ticks. The middle of the best bid and best ask (100.1) is the [mid price](#g-mid), a good guess of what the share is really worth, its [fair value](#g-fair-value).

A trade happens when a buyer and a seller agree on a price. If you send a buy order at 100.2 or higher, you trade immediately with the seller at 100.2: you were the [aggressive](#g-aggressive) side and you [crossed the spread](#g-cross). If you send a buy at 100.1, nobody is selling that cheap, so your order waits in the book: you are [passive](#g-passive), and you trade only when someone sells to you. Orders at the same price wait in a [queue](#g-queue): first come, first served.

What you hold is your [position](#g-position). Bought 10 = long 10 (+10). Sold 10 you did not own = short 10 (-10). [PnL](#g-pnl) (profit and loss) is how much money you have made or lost, counting what your current position is worth.

## This challenge: one company, two listings {#dual}

The challenge (as far as we know before the day) has the same company listed on two markets: a [dual listing](#g-dual-listing). One listing is **busy** ([liquid](#g-liquidity)): lots of traders, tight prices, trades happen all the time. The other is **thin** (illiquid): few traders, wide gaps, and prices that lag behind. In the panel the busy one is called the **primary** (for example ASML) and the thin one the **dual** (for example ASML_DUAL).

Because they are the same company, both listings should be worth the same. When they are not, there is money to be made.

## How the bot makes money {#money}

The bot combines three ideas.

**1. Quoting.** It keeps a waiting buy order a little below fair value and a waiting sell order a little above it on the thin listing. These are its [quotes](#g-quote). Other traders who want to trade on the thin listing trade with us. Each time, we earn the gap between our price and fair value. This is what a [market maker](#g-market-maker) does.

**2. Hedging.** After someone buys from us on the thin listing, we are short. If the price rises, we lose. So the bot immediately buys the same amount on the busy listing. Now we are short on one and long on the other: price moves cancel out. This is a [hedge](#g-hedge). The leftover risk after hedging is the [net delta](#g-net-delta); the bot keeps it near 0.

**3. Arbitrage.** Sometimes someone offers to sell the thin listing below what buyers pay on the busy listing. The bot buys the cheap one and sells the expensive one at once and keeps the difference. This is [arbitrage](#g-arbitrage).

Worked example: fair value is 100.1. Our quote buys on the thin listing at 100.0. Someone sells us 10 lots: we earn about 0.1 per lot against fair value. We hedge by selling 10 on the busy listing. If we can sell there at 100.1 (a waiting order in the middle of the spread) hedging costs nothing; if we must sell at the best bid 100.0 it costs 0.1 per lot and our profit is gone. **The cheaper the hedge, the more we earn.** That single idea drove most improvements.

## Using the panel {#panel}

### The status bar {#bar}

Shows what is running, how long, and the key numbers: PnL, net delta (should be near 0), positions, orders per second, and rejected orders (should be 0).

| Button | What it does | Positions after |
|---|---|---|
| Pause trading | Pulls our quotes; hedging continues. Press again to resume. | Unchanged |
| Stop | Ends the run cleanly, applying your 'When stopping' choice. | Depends on that choice |
| Flatten and stop | Closes every position at market prices, then stops. Asks you to click twice. | All zero |

### Run tab {#tab-run}

Four steps, top to bottom.

1. **What do you want to do?** Observe (watch the real market, no orders), Trade live (real orders), Rehearse (the same thing on a simulated practice market), or Flatten now (close everything).
2. **Strategy.** Pick one of the three strategies, or a preset that fills in tried settings for you. For 'evolved', also pick a [version](#g-version).
3. **Settings.** Grouped by purpose. Every setting shows its plain name, its code name in small print, a one-line explanation, and a **?** for the full story. Blue labels mark values you changed. The essentials are open; rarer ones are under 'Advanced'.
4. **Start.** The box on the right says in one sentence what will happen. Live trading and Flatten ask for a second click. 'Show command' shows the exact command, if you are curious.

Observe, Trade live and Flatten now only work on a computer with the exchange's Optibook client installed (the hackathon machines). Rehearse works everywhere.

### Monitor tab {#tab-monitor}

- **What to do now**: plain-language advice worked out from the latest numbers. Green means nothing needs attention.
- **PnL** chart: profit over time.
- **Positions** chart: what we hold on each listing. The two lines should mirror each other (one up, one down) because of hedging.
- **Prices and our fills**: the mid price of each listing, with a ▲ for each of our buys and a ▼ for each sell.
- **Market and our quotes**: spreads in ticks, how often the two listings are mispriced ('Crossed'), our current quotes, how much rivals offer at our price or better, and trade counts.
- **Where the money comes from**: every trade grouped by why it happened. 'Edge at fill' is what the trade was worth against fair value at that moment. 'After 1 s / 5 s / 30 s' is the same measured later (the [markout](#g-markout)). Positive and green is good. Rows: quote (someone traded with our waiting quote), hedge_passive (a patient hedge), hedge (a hedge that crossed the spread), arb_dual (an arbitrage), flatten (closing positions).
- **Live settings**: change any setting while the bot runs. Edit, then press 'Apply changes'; the bot picks it up within about a second.
- **Health**: orders per second, [rejected](#g-reject) and [throttled](#g-throttle) orders, and how long the bot's loop takes.
- **Events**: settings changes, pauses and errors, newest first.
- **Notes**: write what you see (leaderboard, the brief, what you changed and why). Saved with the run.

### Past runs tab {#tab-runs}

Every run is saved in its own folder with everything the bot saw and did. Click a run for its summary and full report. 'Analyze' writes the report, 'Open in Monitor' shows its charts, 'Download zip' packs it up to share (for example to ask for help).

### Backtest tab {#tab-backtest}

Tries strategy versions or tweaks on practice markets the strategy was never tuned on ([held-out markets](#g-held-out)). Write variants separated by spaces: `v8` is a version; `v10:size=20` is version 10 with quote size 20; `v8:min_profit=0.8,size=5` changes two settings. Results show average PnL, average rank among 13 teams, how often it finished first, PnL compared with the best rival, and the biggest net delta (risk).

## Settings, explained one by one {#settings}

{{PARAMS}}

## Strategies and versions {#strategies}

There are three strategies.

- **cross_arb**: only arbitrage. Trades rarely and safely. Use it first on the day to check that orders and hedges work.
- **quote_hedge**: the original quoting strategy, kept unchanged for comparison.
- **evolved**: the improved quoting strategy. Each version added one improvement found by playing practice rounds and reading the logs.

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
| crowded | 12 rival teams plus the exchange's own traders. The standard. | Practise and compare. |
| crowded_tight | The busy listing's spread is only 1 tick, so hedging always costs something. | Check settings survive a tight market. |
| crowded_sticky | The exchange's traders keep their place in line. | Check gains are not a simulator quirk. |
| crowded_clones | Half the rivals run our own strategy. | See what happens when everyone has the same idea. |
| basic, competitive, hard | Earlier test markets (hard has two companies and a trading halt). | Extra checks. |

The simulated rivals and exchange traders are educated guesses, not the real thing. Use practice results to compare settings, not to predict real profit.

## A plan for the day {#plan}

1. Read the brief. Paste the position limit, the order rate limit and how scoring works into the run's Notes.
2. Run **Observe** for 5 minutes. Open the run in Past runs and press Analyze. Check: which instruments exist, which listing is busy, the spreads, how often they are mispriced.
3. Set **Position limit** and **Order budget** from the brief.
4. Start **Trade live** with **cross_arb** (preset 'Safe start'). Confirm in the Monitor that trades and hedges happen and nothing is rejected.
5. Stop, then start **evolved**: v8 if the busy spread is 1 tick, v10 if it is 2 ticks or more.
6. Watch 'What to do now' and the money table; change settings live. Write every change and the reason in Notes.
7. Before the end, check the brief: if you must end flat, use Flatten and stop.

## If you see this, do that {#playbook}

| What you see | What it means | What to do |
|---|---|---|
| quote 'After 5 s' negative for a while | Prices move against us right after we trade: faster traders pick off our quotes. | Raise Minimum profit per trade (0.5 to 0.8), or lower Quote size. |
| Rejected orders > 0 | The exchange refused orders. The Health box shows why. | Position limit: lower Quote size or Soft limit. Rate limit: lower Order budget. |
| Throttled is high | The bot wanted to send more orders than its budget. | Fine occasionally. If constant, raise Loop period a little. |
| Net delta stays far from 0 | Risk is not being covered. | Check the busy listing is not paused; lower Max unhedged lots. |
| Busy spread is 1 tick | Hedging always costs half a tick. | Use v8 with Quote size 10. Expect smaller profits. |
| Busy spread is 2+ ticks and things go well | Cheap hedging. | Try Quote size 15 (v10). |
| hedge row large and negative | Many hedges had to cross the spread. | Lower Quote size, or raise Hedge patience a little. |
| Positions near the limit | One side may stop quoting. | Lower 'Lean only above'. |
| No quote trades for minutes | Rivals offer better prices, or the market is quiet. | Look at 'Rivals at/better'. Do not chase by dropping Minimum profit below 0.3. |
| Anything strange | | Pause trading, look, then decide. |

## Troubleshooting {#trouble}

- **Observe, Trade live and Flatten now are greyed out.** The Optibook client is not installed on this computer. Run the panel on the hackathon machine. Rehearse still works.
- **The status bar says the panel server is not reachable.** The program behind the panel stopped. Start it again: `python ui/server.py`.
- **The Monitor shows no numbers yet.** The first summary arrives about 10 seconds after starting.
- **Errors in Events.** One bad response does not stop the bot. If errors repeat, Pause, download the run's zip from Past runs, and ask for help.
- **Wrong pairs.** The console prints the pairs the bot found, busy listing first. If it is wrong, type them in 'Pairs' as busy:thin.
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

### Backtest {#g-backtest}
Running a strategy on practice markets to see how it would have done.

### Bid {#g-bid}
A price at which someone is waiting to buy. The best bid is the highest one.

### Cross the spread {#g-cross}
Buying at the best ask or selling at the best bid, so you trade immediately. Costs about half the spread compared with the mid price.

### Crossed (listings) {#g-crossed}
When one listing's best bid is higher than the other listing's best ask, so you could buy on one and sell on the other at a profit. The Monitor shows how often this happens.

### Dual listing {#g-dual-listing}
The same company traded on two markets. Here: the busy primary listing and the thin dual listing.

### Edge {#g-edge}
How much a trade is worth compared with fair value, in ticks. Buying below fair value or selling above it is positive edge.

### Exchange {#g-exchange}
The marketplace that matches buyers and sellers. In the challenge: Optiver's practice exchange, Optibook.

### Fair value {#g-fair-value}
What an instrument is really worth. The bot uses the busy listing's mid price as its best estimate.

### Fill {#g-fill}
A trade that happened to one of our orders. A partial fill trades only part of the order.

### Flatten {#g-flatten}
Closing every position so you hold nothing and have no risk.

### Hedge {#g-hedge}
A second trade that cancels out the price risk of the first. Here: the opposite trade on the other listing.

### Held-out markets {#g-held-out}
Practice markets never used to tune the strategy. Testing on them shows whether an improvement is real or only fits the markets it was tuned on.

### IOC order {#g-ioc}
'Immediate or cancel': trades whatever it can right now and cancels the rest. Never waits in the book. Used for urgent hedges.

### Instrument {#g-instrument}
Anything that can be traded. Each listing (ASML, ASML_DUAL) is its own instrument.

### Inventory {#g-inventory}
Another word for position: what we currently hold.

### Latency {#g-latency}
How long something takes, for example how long the exchange takes to answer an order. Lower is better.

### Limit order {#g-limit-order}
An order with a price limit that waits in the book until someone trades with it or it is cancelled.

### Liquidity {#g-liquidity}
How easy it is to trade without moving the price. A liquid listing has many traders and a tight spread.

### Lot {#g-lot}
The unit of quantity. Here one lot is one share.

### Loop {#g-loop}
One cycle of the bot: look at the market, decide, send orders. It repeats every 'Loop period' seconds.

### Market maker {#g-market-maker}
A trader who always offers to both buy and sell, earning the gap between the two prices.

### Markout {#g-markout}
How much a trade turned out to be worth some seconds later, measured against the fair value at that time. Positive means the price moved our way. Consistently negative means we are being picked off.

### Mid price {#g-mid}
Halfway between the best bid and best ask.

### Net delta {#g-net-delta}
The risk left after hedging: position on the busy listing plus position on the thin listing. Long 30 on one and short 30 on the other gives net delta 0.

### Order {#g-order}
An instruction to buy or sell a number of lots at a price.

### Order book {#g-order-book}
The list of all waiting buy and sell orders for an instrument, sorted by price.

### Passive {#g-passive}
An order that waits in the book for someone else to trade with it. Earns the spread instead of paying it, but may not get filled.

### Pause (instrument) {#g-pause}
The exchange can halt trading in an instrument. The bot pulls its quotes there and hedges elsewhere if needed.

### PnL {#g-pnl}
Profit and loss: money made or lost, including what current positions are worth.

### Position {#g-position}
What you hold. Positive (long) means you own it; negative (short) means you sold more than you owned.

### Position limit {#g-position-limit}
The largest position the rules allow. The exchange refuses orders that could break it.

### Queue {#g-queue}
Orders waiting at the same price, in arrival order. The first in line trades first. Cancelling and re-sending moves you to the back.

### Quote {#g-quote}
Our own waiting buy order and sell order.

### Rate limit {#g-rate-limit}
The most orders per second the exchange accepts from one team.

### Reject {#g-reject}
An order the exchange refused, for example because it could break the position limit or the rate limit.

### Rehearsal {#g-rehearsal}
A run on the simulated practice market, at real speed if you want, with the same screens as live trading.

### Seed {#g-seed}
A number that decides which random practice market you get. Same seed, same market.

### Self-trade {#g-self-trade}
When our own buy order would trade with our own sell order. The exchange blocks it.

### Skew {#g-skew}
Shifting both quotes up or down to make the trades we want more likely, for example to reduce a large position.

### Spread {#g-spread}
The gap between the best ask and the best bid. Narrow spread means a busy, cheap-to-trade market.

### Throttle {#g-throttle}
When the bot holds back an order because it reached its own order budget for that second. Protects us from the exchange's rate limit.

### Tick {#g-tick}
The smallest price step. With a tick of 0.1, prices are 100.0, 100.1, 100.2 and so on.

### Version {#g-version}
A saved stage of the evolved strategy (v0 to v10). Each one added a single tested improvement.
