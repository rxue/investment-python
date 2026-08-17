from collections.abc import Collection
from datetime import date
from enum import StrEnum
from typing import Any

from investment.marketquote import yahoo_finance_fetcher
from investment.vo.value_objects import Price


def fetch_price(symbol: str, target_date: date | None = None) -> Price:
    """Fetch the price for ``symbol``.

    Returns the current quoted price when ``target_date`` is ``None``,
    otherwise the closing price on or before ``target_date``.
    """
    if target_date is None:
        return yahoo_finance_fetcher.fetch_current_price(symbol)
    return yahoo_finance_fetcher.fetcher_close_price(symbol, target_date)


class FundamentalMetric(StrEnum):
    TRAILING_PE = "trailingPE"
    DIVIDEND_YIELD = "dividendYield"
    RETURN_ON_EQUITY = "returnOnEquity"
    REGULAR_MARKET_CHANGE_PERCENT = "regularMarketChangePercent"


def fetch_fundamental_metrics(
    company_symbol: str, metrics: Collection[FundamentalMetric]
) -> dict[str, Any]:
    return yahoo_finance_fetcher.fetch_fundamental_metrics(company_symbol, metrics)
