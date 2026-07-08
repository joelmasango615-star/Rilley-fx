# Trading Bot (multi-asset: stocks, crypto, forex, futures)

A simple, transparent SMA-crossover trading bot with three modes:
**backtest**, **alert**, and **live** (dry-run by default).

Strategy: buy when the fast moving average crosses above the slow one,
sell when it crosses back below. This is a well-known starting point,
not a proven money-maker — expect to tune or replace it.

## Setup

```bash
pip install -r requirements.txt
```

(`yfinance` is required for real data; without it, or if the network
call fails, the bot falls back to synthetic data so you can still test
the logic.)

## 1. Backtest

```bash
# Forex
python main.py backtest --ticker EURUSD=X --fast 20 --slow 50 --period 2y

# Futures (Yahoo Finance continuous contract symbols)
python main.py backtest --ticker CL=F --fast 15 --slow 40   # Crude Oil
python main.py backtest --ticker GC=F --fast 10 --slow 30   # Gold
python main.py backtest --ticker ES=F --fast 20 --slow 50   # S&P 500 E-mini

# Stocks / crypto also work
python main.py backtest --ticker AAPL
python main.py backtest --ticker BTC-USD
```

Reports total return, annualized return/volatility, Sharpe ratio, max
drawdown, win rate, and a buy-and-hold comparison. Add `--save-csv out.csv`
to dump the full bar-by-bar results.

## 2. Alert (check for a fresh signal today)

```bash
python main.py alert --ticker GC=F
python main.py alert --ticker EURUSD=X --webhook https://hooks.slack.com/...
```

Run this on a schedule (cron, GitHub Actions, etc.) to get notified
when a crossover just happened.

## 3. Live trading (crypto via ccxt) — dry-run by default

```bash
# Safe: prints what it WOULD do, sends nothing
python main.py live --ticker BTC/USDT --side buy --qty 0.001

# Real order — requires BOTH flags below
export CONFIRM_LIVE_TRADING=yes
export BINANCE_API_KEY=...
export BINANCE_API_SECRET=...
python main.py live --ticker BTC/USDT --side buy --qty 0.001 --go-live
```

Futures and stock order routing aren't wired up (every broker's API is
different) — `live.py` is a template. For stocks, look at `alpaca-py`;
for futures, your broker's own API (e.g. Interactive Brokers).

## Run it from your phone via GitHub Actions + ntfy

This gets you scheduled signal checks with free push notifications on
your phone. No server, no account, no secrets to configure.

**1. Get notifications (done if you already installed ntfy)**
- Install the **ntfy** app, subscribe to a topic name only you know
  (e.g. `rilleyfx200913`) — that name is your private channel

**2. Put this code in a GitHub repo**
- Create a new repo (can be private) on github.com
- Upload all the files in this folder, keeping the `.github/workflows/`
  folder structure intact

**3. Set your topic name**
- Open `.github/workflows/trading-alert.yml`
- Find the line with `--ntfy-topic "rilleyfx200913"` and replace it
  with your own topic name if different

**4. Edit the schedule / tickers**
- `cron: "5 21 * * 1-5"` is in UTC — convert to your timezone
- Edit the `ticker:` list to whatever you want tracked
  (works for forex `EURUSD=X`, futures `GC=F`, crypto `BTC-USD`, stocks `AAPL`)

**5. Test it**
- Repo → Actions tab → "Trading Alert" workflow → "Run workflow" button
- Check the ntfy app — you should get a notification (or see
  "no new signal" in the run's log if it's a HOLD)

From here it runs automatically on schedule and pushes straight to
your phone. GitHub runs it for free (2,000 free Action-minutes/month
on a private repo, unlimited on public).

## Important caveats

- **Backtests overstate real performance.** Slippage, partial fills,
  market impact, and data-snooping bias aren't fully modeled here.
- **Futures are leveraged** — a small price move creates a large P&L
  swing relative to margin. Position-size accordingly.
- **This is not financial advice**, and I'm not a financial advisor.
  Test extensively in dry-run / paper mode before risking real money,
  and only trade with money you can afford to lose.
- Currency/futures data on Yahoo Finance can be delayed or have gaps —
  don't use it as your sole source for live decisions.

## File map

| File | Purpose |
|---|---|
| `data.py` | Fetches OHLCV data (yfinance), synthetic fallback |
| `strategy.py` | Signal generation (SMA crossover) |
| `backtest.py` | Simulates the strategy, computes metrics |
| `alert.py` | Checks latest bar, sends notifications |
| `live.py` | Order execution, dry-run gated |
| `main.py` | CLI entry point |
