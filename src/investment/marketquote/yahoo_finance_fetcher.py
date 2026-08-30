"""Fetch market quote data from Yahoo Finance via the ``yfinance`` package.

This mirrors the Java `YahooFinanceFetcher`, but delegates all the HTTP
plumbing (cookies, crumbs, endpoint URLs) to ``yfinance`` instead of talking
to the Yahoo Finance REST API directly. Price lookups return raw
``(price, currency, timestamp)`` tuples, leaving ``Price`` value-object
construction (e.g. cent-value conversion) to the caller;
``fetch_fundamental_metrics`` returns a plain ``dict`` keyed by metric name,
since those metric values can be of any type.
"""
from collections.abc import Collection
from datetime import date, timedelta
from typing import Any

import numpy
import pandas
import yfinance as yf

REGULAR_MARKET_CHANGE_PERCENT = "regularMarketChangePercent"


def fetch_current_price(symbol: str) -> tuple[float, str, int]:
    """Fetch the latest quoted price for ``symbol``.

    Returns a ``(price, currency, timestamp)`` tuple: ``price`` is the
    fetched price as returned by ``yfinance`` (a ``float``), ``currency``
    is the quote currency, and ``timestamp`` is the quote time as Unix
    epoch seconds.
    """
    info = yf.Ticker(symbol).info
    price = info.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"Cannot fetch any price with the given company symbol {symbol}")

    currency:str|None = info.get("currency")
    regular_market_time = info.get("regularMarketTime")
    if currency is None or regular_market_time is None:
        raise ValueError(
            f"Cannot determine the price currency or the timestamp for company symbol {symbol}"
        )

    return price, currency, regular_market_time


def fetcher_close_price(
    symbol: str, target_date: date
) -> tuple[numpy.float64, str, pandas.Timestamp]:
    """Fetch the closing price for ``symbol`` on or before ``target_date``.

    Returns a ``(price, currency, timestamp)`` tuple: ``price`` is the
    closing price as returned by ``yfinance``, ``currency`` is the quote
    currency, and ``timestamp`` is the close date/time.
    """
    ticker = yf.Ticker(symbol)
    history = ticker.history(
        start=target_date - timedelta(days=7),
        end=target_date + timedelta(days=1),
        interval="1d",
    )
    history = history[pandas.DatetimeIndex(history.index).date <= target_date]
    if history.empty:
        raise ValueError(
            f"No historical price found for company symbol {symbol} on or before {target_date}"
        )

    last_close = history["Close"].iloc[-1]
    timestamp = history.index[-1]

    currency = ticker.info.get("currency")
    if currency is None:
        raise ValueError(f"Cannot determine the price currency for company symbol {symbol}")

    return last_close, currency, timestamp

def fetcher_close_prices(
    symbols: list[str], target_date: date
) -> dict[str, tuple[numpy.float64, str, pandas.Timestamp]]:
    """Fetch the closing price for each of ``symbols`` on or before ``target_date``.

    Unlike :func:`fetcher_close_price`, this batches the price history fetch
    for all ``symbols`` into a single ``yfinance.download`` call. Returns a
    dict mapping each symbol to a ``(price, currency, timestamp)`` tuple, the
    same shape returned by :func:`fetcher_close_price`.
    """
    if not symbols:
        return {}

    data = yf.download(
        symbols,
        start=target_date - timedelta(days=7),
        end=target_date + timedelta(days=1),
        interval="1d",
        group_by="ticker",
        progress=False,
    )
    if data is None:
        raise ValueError(
            f"No historical price found for company symbols {symbols} on or before {target_date}"
        )

    result: dict[str, tuple[numpy.float64, str, pandas.Timestamp]] = {}
    for symbol in symbols:
        history = data[symbol]
        history = history[pandas.DatetimeIndex(history.index).date <= target_date]
        history = history[history["Close"].notna()]
        if history.empty:
            raise ValueError(
                f"No historical price found for company symbol {symbol} on or before {target_date}"
            )

        last_close = history["Close"].iloc[-1]
        timestamp = history.index[-1]

        currency = yf.Ticker(symbol).info.get("currency")
        if currency is None:
            raise ValueError(f"Cannot determine the price currency for company symbol {symbol}")

        result[symbol] = (last_close, currency, timestamp)

    return result


def fetch_price_history(symbol: str, start: date, end: date) -> tuple[dict[date, float], str]:
    """Fetch daily closing prices for ``symbol`` between ``start`` and ``end`` (inclusive).

    Returns a ``(prices, currency)`` tuple: ``prices`` maps each trading date
    in the range to its closing price, and ``currency`` is the quote currency.
    """
    ticker = yf.Ticker(symbol)
    history = ticker.history(
        start=start,
        end=end + timedelta(days=1),
        interval="1d",
    )
    if history.empty:
        raise ValueError(
            f"No historical price found for company symbol {symbol} between {start} and {end}"
        )

    dates = pandas.DatetimeIndex(history.index).date
    prices = {
        trading_date: float(close)
        for trading_date, close in zip(dates, history["Close"], strict=True)
    }

    currency = ticker.info.get("currency")
    if currency is None:
        raise ValueError(f"Cannot determine the price currency for company symbol {symbol}")

    return prices, currency


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
