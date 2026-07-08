"""
backtest.py — simulate a strategy over historical data and score it.

Assumptions (change to fit reality):
  - Trade at the Close price on the signal bar (no slippage modeled by default)
  - No leverage, one position at a time, fully in or fully out
  - `fee_bps` = round-trip cost in basis points, applied per trade
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def run_backtest(
    df_with_signals: pd.DataFrame,
    initial_capital: float = 10_000.0,
    fee_bps: float = 5.0,
) -> tuple[pd.DataFrame, dict]:
    df = df_with_signals.copy()
    df["daily_return"] = df["Close"].pct_change().fillna(0)

    # strategy is "in the market" using yesterday's position (avoid lookahead)
    df["strategy_return"] = df["daily_return"] * df["position"].shift(1).fillna(0)

    # apply trading cost whenever a trade happens
    trades = df["signal"].isin(["BUY", "SELL"])
    fee = fee_bps / 10_000
    df.loc[trades, "strategy_return"] -= fee

    df["equity"] = initial_capital * (1 + df["strategy_return"]).cumprod()
    df["buy_hold_equity"] = initial_capital * (1 + df["daily_return"]).cumprod()

    metrics = _compute_metrics(df, initial_capital)
    return df, metrics


def _compute_metrics(df: pd.DataFrame, initial_capital: float) -> dict:
    final_equity = df["equity"].iloc[-1]
    total_return = final_equity / initial_capital - 1

    daily = df["strategy_return"]
    ann_factor = 252
    ann_return = (1 + daily.mean()) ** ann_factor - 1
    ann_vol = daily.std() * np.sqrt(ann_factor)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    running_max = df["equity"].cummax()
    drawdown = (df["equity"] - running_max) / running_max
    max_drawdown = drawdown.min()

    n_trades = df["signal"].isin(["BUY", "SELL"]).sum()

    trade_returns = []
    entry_price = None
    for _, row in df.iterrows():
        if row["signal"] == "BUY":
            entry_price = row["Close"]
        elif row["signal"] == "SELL" and entry_price is not None:
            trade_returns.append(row["Close"] / entry_price - 1)
            entry_price = None
    win_rate = (np.mean([r > 0 for r in trade_returns]) if trade_returns else 0.0)

    buy_hold_return = df["buy_hold_equity"].iloc[-1] / initial_capital - 1

    return {
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return * 100, 2),
        "annualized_return_pct": round(ann_return * 100, 2),
        "annualized_volatility_pct": round(ann_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "num_trades": int(n_trades),
        "win_rate_pct": round(win_rate * 100, 2),
        "buy_hold_return_pct": round(buy_hold_return * 100, 2),
    }
