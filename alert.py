"""
alert.py — check the most recent bar for a fresh signal and notify.

Notification is pluggable. Console print always works. Webhook/email
are stubbed in — fill in your own URL/credentials to use them.
"""

from __future__ import annotations
import pandas as pd


def check_latest_signal(df_with_signals: pd.DataFrame, ticker: str) -> str | None:
    """Returns 'BUY', 'SELL', or None based on the most recent bar."""
    latest = df_with_signals.iloc[-1]
    signal = latest["signal"]
    if signal in ("BUY", "SELL"):
        return signal
    return None


def notify_console(ticker: str, signal: str, price: float, when: pd.Timestamp) -> None:
    print(f"[ALERT] {when.date()}  {ticker}: {signal} @ {price:.2f}")


def notify_ntfy(topic: str, ticker: str, signal: str, price: float) -> None:
    """
    Posts a push notification via ntfy.sh — no account, no auth, no
    webhook setup. Just PUTs/POSTs plain text to https://ntfy.sh/<topic>
    and anyone subscribed to that topic on the ntfy app gets it instantly.
    """
    import requests
    title = f"{ticker}: {signal}"
    body = f"{signal} signal at {price:.2f}"
    resp = requests.post(
        f"https://ntfy.sh/{topic}",
        data=body.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "high" if signal == "BUY" else "default",
            "Tags": "chart_with_upwards_trend" if signal == "BUY" else "chart_with_downwards_trend",
        },
        timeout=10,
    )
    resp.raise_for_status()


def run_alert_check(ticker: str, df_with_signals: pd.DataFrame, ntfy_topic: str | None = None) -> None:
    signal = check_latest_signal(df_with_signals, ticker)
    latest = df_with_signals.iloc[-1]
    if signal:
        notify_console(ticker, signal, latest["Close"], df_with_signals.index[-1])
        if ntfy_topic:
            notify_ntfy(ntfy_topic, ticker, signal, latest["Close"])
    else:
        print(f"[alert] {ticker}: no new signal as of {df_with_signals.index[-1].date()} (HOLD)")
