# What the Bona Fide Optibook site tells us (read 11 Nov 2026, evening before the event)

Source: https://2026-bona-fide.optibook.net (docs, FAQ, setup, intro exercises, lectures, visualizer).
The team challenge brief and the Dev Environment only unlock after joining a team, so instruments, limits and
scoring for the real round may still differ from the practice market below.

## Practice market right now (visualizer)
- 8 stocks, all status Open: AMD ~163, AVGO ~207, CRWV ~143, MU ~78, NBIS ~93, NVDA ~124, SNDK ~53, VRT ~65.
  Not a dual listing. AI / semiconductor names, so natural pairs exist by sector:
  NVDA/AMD/AVGO (chips), MU/SNDK (memory), CRWV/NBIS (AI cloud), VRT (data-centre power).
- Prices quoted to 0.1, so the tick is most likely 0.1.
- One big maker bot per book: 3 levels per side, 1000/2000/3000 lots, about 4 ticks wide (e.g. bid 162.7, ask 163.1).
  Thinner names (CRWV, NBIS, SNDK) show 1000 lots and wider spreads (up to ~1.3).
- Only 4 participants trade (JazzyJellies, GroovyGrapefruits, PrudentPoultry, LivelyLasagnas), always in fixed pairs,
  always 20 lots, about 100 trades a minute in total. These are background bots.
- 50 seconds of mid prices: no clear co-movement between any two names (correlations -0.43 to 0.47, too short to trust).
- Instrument statuses: Open, Paused, Expired. Leaderboard columns: PnL, Hourly PnL, Delta, Cash Delta, Position,
  Vega, Hourly Sharpe, PnL graph. Vega and Hourly Sharpe suggest options and risk-adjusted scoring may appear.

## Rules and behaviour (FAQ)
- One connection per team. A new connection kicks the old one. Our separate `--observe` process would kick the bot.
- No manual disconnect: when the program stops, the exchange cancels all its orders (Cancel On Disconnect).
- Trade ticks start empty after connecting; there is no history snapshot.
- No fill notifications: poll `poll_new_trades` or watch positions.
- PnL = realised cash + positions valued at the last traded price (get_pnl can take other valuations).
- Position limits per instrument; a trade that would breach is refused (example given: +/-300). Check the brief.
- In a dual listing, positions cannot be transferred between instruments.

## Client API (docs) beyond what we already use
- `get_tradable_instruments()` excludes expired and paused instruments.
- `Instrument` carries tick_size, instrument_type (STOCK, STOCK_FUTURE, STOCK_OPTION, INDEX_FUTURE, INDEX_OPTION,
  INDEX_TRACKING_ETF), price_change_limit (absolute and relative), expiry, option_kind, strike, base_instrument_id,
  interest_rate, index_constituents / divisor / volatility, etf_cash_comp, etf_multiplier, instrument_group.
- `poll_new_social_media_feeds()` / `get_social_media_feeds_history()` return posts with timestamp and meta_data:
  a news feed that can move prices.
- `get_cash()`, `get_positions_and_cash()`, `get_trade_history()`, `get_trade_tick_history()`.
- `amend_order` changes volume only (no price), as our sim already assumes.
- `optibook.exporter.Exporter` writes CSVs in the dev environment.

## Environment
- Code runs in a browser VS Code ("Dev Environment") opened from the Teams page, with the client preinstalled and
  `your_optiver_workspace/optibook_guides/code_snippets.ipynb`.
- Lectures: market basics, order books, pairs trading, portfolio values, then options, pricing, volatility, Greeks.
