# Getting the bot into the Dev Environment (about 5 minutes)

The exchange is only reachable from Optiver's browser VS Code ("Dev Environment", opened from the Teams page).
Your laptop only needs a browser.

## 1. Copy the code in (pick the first that works)

1. **git** (fastest if the Dev Environment can reach GitHub). In its terminal:
   `git clone https://github.com/zain1290/optibook-hackathon.git`
   The repo is private: when asked for a password, paste a GitHub token
   (GitHub > Settings > Developer settings > Fine-grained tokens > only this repo, read-only, expires tomorrow).
2. **Upload the zip.** On your laptop: `python tools/make_bundle.py`, then drag `dist/optibook-bot.zip` into the
   VS Code file explorer and run `unzip optibook-bot.zip` in its terminal.
3. **Paste.** If uploads are blocked: open `dist/install_paste.py` on your laptop, copy everything, create a new
   file `install_paste.py` in VS Code, paste, save, run `python install_paste.py`.

Then `cd optibook-bot` (or `cd optibook-hackathon`).

## 2. Check it before trading (2 minutes)

- `python -m pytest -q tests`: everything should pass (only needs Python 3.8+; `pair_stats.py` needs 3.10+).
- Stop anything else that is connected (the code_snippets notebook too). **Only one connection per team.**
- `python tools/intro_exercises.py`: buys and sells 1 lot, tries an amend and cancel, prints the instrument fields,
  error texts, latency and news format. Paste its summary into the chat / notes.md.
- Optional: `python tools/intro_exercises.py --probe-rate` measures the order rate limit with 1-lot orders that
  cannot trade.

## 3. Observe, then trade

- `python run_live.py --observe --minutes 5`: records the market without sending orders.
  Then `python tools/analyze_run.py` (latest run), `python tools/pair_stats.py logs/<run>`,
  `python tools/news_impact.py logs/<run>`.
- Set the limits from the brief, e.g. `-p position_limit=300 -p max_ops_per_sec=20` (stay under the real limit).
- Start small: `python run_live.py --strategy combo -p size=5`, watch for 2 minutes, then raise size.
- Panic: `python run_live.py --flatten` (cancels everything, closes all positions). Ctrl+C also closes positions.

## 4. The control panel (optional)

`python ui/server.py --no-browser` starts it on port 8050 inside the Dev Environment. VS Code usually offers
"Open in browser" for the port (or try `<dev environment url>/proxy/8050/`). The panel uses relative links, so it
works behind that proxy. If it doesn't open, use the commands above; the panel is a convenience, not a requirement.

## If something goes wrong

| You see | Do |
|---|---|
| "someone was already connected" | Fine, you are connected now; make sure only one program runs. |
| `connection lost ... reconnecting` | The bot reconnects by itself; the exchange cancelled our orders, it re-quotes. |
| "Another live program (pid ...) already holds the connection" | Stop the other program, or `--force` if it is dead. |
| Many rejects | Read the reason in the console; rate limit -> lower `max_ops_per_sec`; position -> check `position_limit`. |
| PnL drops fast | Pause (settings `"pause": true` or the panel), look at the monitor's "where the money comes from". |
