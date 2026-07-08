"""
live.py — order execution layer.

SAFETY DEFAULTS:
  - `dry_run=True` unless you explicitly pass dry_run=False AND set
    CONFIRM_LIVE_TRADING=yes in your environment. This is a deliberate
    double gate so a stray flag or config bug can't send real orders.
  - You must supply your own broker/exchange API keys as environment
    variables. None are included here.

This module is a template, not a finished integration. Order routing,
symbol formatting, minimum size, and error handling differ per broker —
read your broker's API docs before flipping dry_run off.

Supported backends (install the one you need):
  - crypto exchanges via `ccxt`      (pip install ccxt)
  - US stocks via `alpaca-py`        (pip install alpaca-py)
"""

from __future__ import annotations
import os


class LiveTrader:
    def __init__(self, backend: str, dry_run: bool = True):
        self.backend = backend
        self.dry_run = dry_run
        if not dry_run and os.environ.get("CONFIRM_LIVE_TRADING") != "yes":
            raise RuntimeError(
                "Refusing to trade live: set dry_run=True, or set the "
                "environment variable CONFIRM_LIVE_TRADING=yes if you have "
                "read the risks and really mean it."
            )
        self._client = None

    def _connect_ccxt(self, exchange_id: str):
        import ccxt
        api_key = os.environ.get(f"{exchange_id.upper()}_API_KEY")
        api_secret = os.environ.get(f"{exchange_id.upper()}_API_SECRET")
        if not api_key or not api_secret:
            raise RuntimeError(
                f"Set {exchange_id.upper()}_API_KEY / {exchange_id.upper()}_API_SECRET "
                "environment variables first."
            )
        exchange_class = getattr(ccxt, exchange_id)
        client = exchange_class({"apiKey": api_key, "secret": api_secret})
        # Use exchange's sandbox/testnet where available:
        if hasattr(client, "set_sandbox_mode"):
            client.set_sandbox_mode(True)
        return client

    def place_order(self, symbol: str, side: str, qty: float) -> dict:
        """
        side: 'buy' or 'sell'
        qty: units of the asset (not dollars)
        """
        if self.dry_run:
            msg = f"[DRY RUN] Would {side.upper()} {qty} {symbol}"
            print(msg)
            return {"status": "dry_run", "symbol": symbol, "side": side, "qty": qty}

        if self.backend == "ccxt":
            if self._client is None:
                raise RuntimeError("Call _connect_ccxt(exchange_id) first.")
            order = self._client.create_order(symbol, type="market", side=side, amount=qty)
            return order

        raise NotImplementedError(f"Backend '{self.backend}' not wired up yet.")
