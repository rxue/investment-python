"""Fetch market quote data from Yahoo Finance via the ``yfinance`` package.

This mirrors the Java `YahooFinanceFetcher`, but delegates all the HTTP
plumbing (cookies, crumbs, endpoint URLs) to ``yfinance`` instead of talking
to the Yahoo Finance REST API directly. Price lookups return the ``Price``
value object; ``fetch_fundamental_metrics`` still returns a plain ``dict``
keyed by metric name, since those metric values can be of any type.
"""
from collections.abc import Collection
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from zoneinfo import ZoneInfo

import yfinance as yf

from investment.vo.value_objects import Price

REGULAR_MARKET_CHANGE_PERCENT = "regularMarketChangePercent"


def _to_cent_value(price: Any) -> int:
    """Convert a fractional price (e.g. ``189.98``) to whole cents."""
    return int((Decimal(str(price)) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def fetch_current_price(symbol: str) -> Price:
    """Fetch the latest quoted price for ``symbol``."""
    info = yf.Ticker(symbol).info
    price = info.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"Cannot fetch any price with the given company symbol {symbol}")

    regular_market_time = info.get("regularMarketTime")
    exchange_timezone_name = info.get("exchangeTimezoneName")
    if regular_market_time is None or exchange_timezone_name is None:
        raise ValueError(f"Cannot determine the price timestamp for company symbol {symbol}")
    timestamp = datetime.fromtimestamp(regular_market_time, tz=ZoneInfo(exchange_timezone_name))

    return Price(
        cent_value=_to_cent_value(price),
        currency=info.get("currency"),
        timestamp=timestamp,
    )


def fetcher_close_price(symbol: str, target_date: date) -> Price:
    """Fetch the closing price for ``symbol`` on or before ``target_date``."""
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

    return Price(
        cent_value=_to_cent_value(last_close),
        currency=ticker.info.get("currency"),
        timestamp=timestamp,
    )


def fetch_fundamental_metrics(symbol: str, metrics: Collection[str]) -> dict[str, Any]:
    """Fetch fundamental metrics (e.g. ``trailingPE``, ``dividendYield``,
    ``returnOnEquity``, ``regularMarketChangePercent``) for ``symbol``.

    Unlike the Yahoo Finance REST API, ``yfinance``'s ``Ticker.info`` already
    flattens the various quote-summary modules (summaryDetail, financialData,
    price, ...) into a single dict, so metric names can be looked up directly
    without mapping each one to its containing section.
    """
    if not metrics:
        return {}

    info = yf.Ticker(symbol).info
    return {metric_name: info.get(metric_name) for metric_name in metrics}
