from collections.abc import Collection
from datetime import date
from enum import Enum
from types import MappingProxyType
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


class Metric(Enum):
    PRICE = None
    TRAILING_PE = "trailingPE"
    DIVIDEND_YIELD = "dividendYield"
    RETURN_ON_EQUITY = "returnOnEquity"
    REGULAR_MARKET_CHANGE_PERCENT = "regularMarketChangePercent"

    def __init__(self, yahoo_metric_name: str | None = None) -> None:
        self.yahoo_metric_name = yahoo_metric_name


def fetch_fundamental_metrics(
    company_symbol: str, metrics: Collection[Metric]
) -> dict[str, Any]:
    return yahoo_finance_fetcher.fetch_fundamental_metrics(company_symbol, metrics)


def fetch_current_metrics(
        company_symbol: str, metrics: Collection[Metric]
) -> dict[str, Any]:
    fundamental_metrics = [metric.yahoo_metric_name for metric in metrics if metric is not Metric.PRICE]
    fundamental_metrics_values = yahoo_finance_fetcher.fetch_fundamental_metrics(company_symbol, fundamental_metrics)

    combined_metrics: dict[str, Any] = dict(fundamental_metrics_values)
    if Metric.PRICE in metrics:
        combined_metrics[Metric.PRICE] = fetch_price(company_symbol)
    return MappingProxyType(combined_metrics)
