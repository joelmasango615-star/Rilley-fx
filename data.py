"""
data.py — price data fetching.

Real data uses yfinance (works for stocks, ETFs, crypto like BTC-USD,
and forex pairs like EURUSD=X). If yfinance isn't installed or a
network call fails, falls back to synthetic random-walk data so you
can still test the bot's logic offline.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a ticker.

    ticker examples:
        Stocks:  AAPL, MSFT, TSLA
        Crypto:  BTC-USD, ETH-USD
        Forex:   EURUSD=X, GBPUSD=X

    Returns a DataFrame indexed by date with columns:
        Open, High, Low, Close, Volume
    """
    try:
        import yfinance as yf
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            raise ValueError(f"No data returned for {ticker}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"[data] Live fetch failed ({e}). Using synthetic data instead.")
        return _synthetic_ohlcv(ticker)


def _synthetic_ohlcv(ticker: str, n: int = 252, seed: int | None = None) -> pd.DataFrame:
    """Generate a plausible random-walk price series for offline testing."""
    rng = np.random.default_rng(seed if seed is not None else abs(hash(ticker)) % (2**32))
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n)
    returns = rng.normal(loc=0.0004, scale=0.015, size=n)
    close = 100 * np.exp(np.cumsum(returns))
    high = close * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.004, n)))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    volume = rng.integers(1_000_000, 10_000_000, n)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
