"""
main.py — command-line entry point.

Examples
--------
Backtest a forex pair:
    python main.py backtest --ticker EURUSD=X --fast 20 --slow 50

Backtest a futures contract:
    python main.py backtest --ticker CL=F --fast 10 --slow 30

Check today's signal (alert mode) for gold futures:
    python main.py alert --ticker GC=F

Live trade (crypto, dry run by default):
    python main.py live --ticker BTC/USDT --side buy --qty 0.001
"""

from __future__ import annotations
import argparse

from data import fetch_ohlcv
from strategy import STRATEGIES
from backtest import run_backtest
from alert import run_alert_check
from live import LiveTrader


# Common futures & forex tickers on Yahoo Finance, for reference:
FUTURES_EXAMPLES = {
    "ES=F": "S&P 500 E-mini",
    "NQ=F": "Nasdaq 100 E-mini",
    "CL=F": "Crude Oil WTI",
    "GC=F": "Gold",
    "SI=F": "Silver",
    "ZC=F": "Corn",
    "6E=F": "Euro FX futures",
}
FOREX_EXAMPLES = {
    "EURUSD=X": "Euro / US Dollar",
    "GBPUSD=X": "British Pound / US Dollar",
    "USDJPY=X": "US Dollar / Japanese Yen",
    "AUDUSD=X": "Australian Dollar / US Dollar",
}


def cmd_backtest(args):
    df = fetch_ohlcv(args.ticker, period=args.period, interval=args.interval)
    signal_fn = STRATEGIES[args.strategy]
    df = signal_fn(df, fast=args.fast, slow=args.slow)
    result_df, metrics = run_backtest(df, initial_capital=args.capital, fee_bps=args.fee_bps)

    print(f"\n=== Backtest: {args.ticker} ({args.strategy}, fast={args.fast}, slow={args.slow}) ===")
    for k, v in metrics.items():
        print(f"{k:28s} {v}")
    print()
    if args.save_csv:
        result_df.to_csv(args.save_csv)
        print(f"Saved full results to {args.save_csv}")


def cmd_alert(args):
    df = fetch_ohlcv(args.ticker, period="6mo", interval=args.interval)
    signal_fn = STRATEGIES[args.strategy]
    df = signal_fn(df, fast=args.fast, slow=args.slow)
    run_alert_check(args.ticker, df, ntfy_topic=args.ntfy_topic)


def cmd_live(args):
    trader = LiveTrader(backend="ccxt", dry_run=not args.go_live)
    trader.place_order(args.ticker, args.side, args.qty)


def build_parser():
    p = argparse.ArgumentParser(description="Simple multi-asset trading bot (educational).")
    sub = p.add_subparsers(dest="command", required=True)

    common = dict(
        fast=("--fast", int, 20, "Fast SMA window"),
        slow=("--slow", int, 50, "Slow SMA window"),
    )

    bt = sub.add_parser("backtest", help="Backtest a strategy on historical data")
    bt.add_argument("--ticker", required=True, help="e.g. AAPL, BTC-USD, EURUSD=X, CL=F")
    bt.add_argument("--period", default="2y", help="yfinance period, e.g. 6mo, 1y, 2y, 5y")
    bt.add_argument("--interval", default="1d", help="yfinance interval, e.g. 1d, 1h")
    bt.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    bt.add_argument("--fast", type=int, default=20)
    bt.add_argument("--slow", type=int, default=50)
    bt.add_argument("--capital", type=float, default=10_000.0)
    bt.add_argument("--fee-bps", type=float, default=5.0, dest="fee_bps")
    bt.add_argument("--save-csv", default=None, dest="save_csv")
    bt.set_defaults(func=cmd_backtest)

    al = sub.add_parser("alert", help="Check for a fresh signal right now")
    al.add_argument("--ticker", required=True)
    al.add_argument("--interval", default="1d")
    al.add_argument("--strategy", default="sma_crossover", choices=STRATEGIES.keys())
    al.add_argument("--fast", type=int, default=20)
    al.add_argument("--slow", type=int, default=50)
    al.add_argument("--ntfy-topic", default=None, dest="ntfy_topic", help="Your ntfy.sh topic name, e.g. rilleyfx200913")
    al.set_defaults(func=cmd_alert)

    lv = sub.add_parser("live", help="Place an order (dry-run unless --go-live)")
    lv.add_argument("--ticker", required=True, help="Exchange symbol, e.g. BTC/USDT (ccxt format)")
    lv.add_argument("--side", required=True, choices=["buy", "sell"])
    lv.add_argument("--qty", required=True, type=float)
    lv.add_argument("--go-live", action="store_true", help="Actually send the order (needs CONFIRM_LIVE_TRADING=yes)")
    lv.set_defaults(func=cmd_live)

    return p


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
