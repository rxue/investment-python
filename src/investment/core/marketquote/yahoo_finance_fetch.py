"""Fetch market quote data from Yahoo Finance via the ``yfinance`` package.

This mirrors the Java `YahooFinanceFetcher`, but delegates all the HTTP
plumbing (cookies, crumbs, endpoint URLs) to ``yfinance`` instead of talking
to the Yahoo Finance REST API directly. Results are plain ``dict``s keyed by
metric name rather than dedicated value objects, since the metric values can
be of any type.
"""

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import yfinance as yf

REGULAR_MARKET_CHANGE_PERCENT = "regularMarketChangePercent"


def get_current_price(symbol: str) -> dict[str, Any]:
    """Fetch the latest quoted price for ``symbol``.

    Returns a dict with ``currency``, ``price`` and ``timestamp`` keys.
    """
    info = yf.Ticker(symbol).info
    price = info.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"Cannot fetch any price with the given company symbol {symbol}")

    timestamp = None
    regular_market_time = info.get("regularMarketTime")
    exchange_timezone_name = info.get("exchangeTimezoneName")
    if regular_market_time is not None and exchange_timezone_name is not None:
        timestamp = datetime.fromtimestamp(
            regular_market_time, tz=ZoneInfo(exchange_timezone_name)
        )

    return {
        "currency": info.get("currency"),
        "price": price,
        "timestamp": timestamp,
    }


def get_close_price(symbol: str, target_date: date) -> dict[str, Any]:
    """Fetch the closing price for ``symbol`` on or before ``target_date``.

    Returns a dict with ``currency``, ``price`` and ``timestamp`` keys.
    """
    ticker = yf.Ticker(symbol)
    history = ticker.history(
        start=target_date - timedelta(days=7),
        end=target_date + timedelta(days=1),
        interval="1d",
    )
    history = history[history.index.date <= target_date]
    if history.empty:
        raise ValueError(
            f"No historical price found for company symbol {symbol} on or before {target_date}"
        )

    last_close = history["Close"].iloc[-1]
    timestamp = history.index[-1].to_pydatetime()

    return {
        "currency": ticker.info.get("currency"),
        "price": last_close,
        "timestamp": timestamp,
    }


def get_fundamentals(symbol: str, metric_names: list[str]) -> dict[str, Any]:
    """Fetch fundamental metrics (e.g. ``trailingPE``, ``dividendYield``,
    ``returnOnEquity``, ``regularMarketChangePercent``) for ``symbol``.

    Unlike the Yahoo Finance REST API, ``yfinance``'s ``Ticker.info`` already
    flattens the various quote-summary modules (summaryDetail, financialData,
    price, ...) into a single dict, so metric names can be looked up directly
    without mapping each one to its containing section.
    """
    if not metric_names:
        return {}

    info = yf.Ticker(symbol).info
    return {metric_name: info.get(metric_name) for metric_name in metric_names}
