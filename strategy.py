"""
strategy.py — trading signal logic.

Default strategy: SMA crossover.
  - Fast SMA crosses ABOVE slow SMA  -> BUY signal
  - Fast SMA crosses BELOW slow SMA  -> SELL signal

This is a simple, well-known starting point — not a proven money-maker.
Swap in your own rules by writing a function with the same signature.
"""

from __future__ import annotations
import pandas as pd


def sma_crossover_signals(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    """
    Adds columns: sma_fast, sma_slow, position (1=long, 0=flat), signal (BUY/SELL/HOLD)
    """
    out = df.copy()
    out["sma_fast"] = out["Close"].rolling(fast).mean()
    out["sma_slow"] = out["Close"].rolling(slow).mean()

    out["position"] = 0
    out.loc[out["sma_fast"] > out["sma_slow"], "position"] = 1

    # signal fires only on the bar the crossover happens
    prev_position = out["position"].shift(1).fillna(0)
    out["signal"] = "HOLD"
    out.loc[(out["position"] == 1) & (prev_position == 0), "signal"] = "BUY"
    out.loc[(out["position"] == 0) & (prev_position == 1), "signal"] = "SELL"

    return out


STRATEGIES = {
    "sma_crossover": sma_crossover_signals,
}
