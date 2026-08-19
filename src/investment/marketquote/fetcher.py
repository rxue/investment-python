from collections.abc import Collection
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from types import MappingProxyType
from typing import Any

from investment.marketquote import yahoo_finance_fetcher
from investment.marketquote.metrics import Metric, MetricsRecord
from investment.vo.value_objects import Price



def fetch_price(symbol: str, target_date: date | None = None) -> Price:
    """Fetch the price for ``symbol``.

    Returns the current quoted price when ``target_date`` is ``None``,
    otherwise the closing price on or before ``target_date``.
    """
    if target_date is None:
        return yahoo_finance_fetcher.fetch_current_price(symbol)
    return yahoo_finance_fetcher.fetcher_close_price(symbol, target_date)


def fetch_fundamental_metrics(
    company_symbol: str, metrics: Collection[Metric]
) -> dict[str, Any]:
    return yahoo_finance_fetcher.fetch_fundamental_metrics(company_symbol, metrics)


def fetch_current_metrics(
        company_symbol: str, metrics: Collection[Metric]
) -> MetricsRecord:
    fundamental_metrics_by_yahoo_name = {
        metric.yahoo_metric_name: metric for metric in metrics if metric is not Metric.PRICE
    }
    fundamental_metrics_values = yahoo_finance_fetcher.fetch_fundamental_metrics(
        company_symbol, fundamental_metrics_by_yahoo_name.keys()
    )

    combined_metrics: dict[Metric, Any] = {
        fundamental_metrics_by_yahoo_name[yahoo_metric_name]: value
        for yahoo_metric_name, value in fundamental_metrics_values.items()
    }
    if Metric.PRICE in metrics:
        combined_metrics[Metric.PRICE] = fetch_price(company_symbol)
    return MetricsRecord(company_id=company_symbol, metrics=MappingProxyType(combined_metrics))

def fetch_current_metrics_batch(
        company_ids: Collection[str], metrics: Collection[Metric], in_multi_threads: bool
) -> list[MetricsRecord]:
    if in_multi_threads:
        company_ids = list(company_ids)
        if not company_ids:
            return []
        with ThreadPoolExecutor(max_workers=min(len(company_ids), 10)) as executor:
            return list(
                executor.map(lambda company_id: fetch_current_metrics(company_id, metrics), company_ids)
            )
    return [fetch_current_metrics(company_id, metrics) for company_id in company_ids]