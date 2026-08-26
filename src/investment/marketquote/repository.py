from collections.abc import Collection
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType
from typing import Any

from investment.marketquote import yahoo_finance_fetcher
from investment.marketquote.fx_rate_fetcher import fetch_fx_rate_to_euro
from investment.marketquote.metrics import Metric, MetricsRecord
from investment.vo.value_objects import Percentage, Price


def fetch_price(symbol: str, target_date: date | None = None) -> Price:
    """Fetch the price for ``symbol``.

    Returns the current quoted price when ``target_date`` is ``None``,
    otherwise the closing price on or before ``target_date``.
    """
    if target_date is None:
        price, currency, epoch_seconds = yahoo_finance_fetcher.fetch_current_price(symbol)
        cent_value = int((Decimal(str(price)) * 100).to_integral_value(rounding=ROUND_HALF_UP))
        return Price(
            cent_value=cent_value,
            currency=currency,
            timestamp=datetime.fromtimestamp(epoch_seconds, tz=timezone.utc),
        )
    last_close, currency, timestamp = yahoo_finance_fetcher.fetcher_close_price(symbol, target_date)
    cent_value = int((Decimal(str(last_close)) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return Price(
        cent_value=cent_value,
        currency=currency,
        timestamp=timestamp,
    )

def fetch_price_in_euro(
    company_id: str, target_date: date | None = None, existing_price: Price | None = None
) -> Price:
    price = existing_price if existing_price is not None else fetch_price(company_id, target_date)
    currency = price.currency_value()
    if currency == 'EURO':
        return price
    else:
        _, fx_rate = fetch_fx_rate_to_euro(currency, date.today())
        price_value = round(price.cent_value / fx_rate)
        return Price(price_value, "EUR", price.timestamp)


def fetch_current_metrics(
        company_id: str, metrics: Collection[Metric]
) -> MetricsRecord:
    def fetch_fundamental_metrics() -> dict[Metric,Any]:
        fundamental_metrics_by_yahoo_name = {
            metric.yahoo_metric_name: metric
            for metric in metrics
            if metric not in [Metric.PRICE, Metric.PRICE_IN_EURO]
            and metric.yahoo_metric_name is not None
        }
        fundamental_metrics_values = yahoo_finance_fetcher.fetch_fundamental_metrics(
            company_id, fundamental_metrics_by_yahoo_name.keys()
        )
        fundamenal_metrics: dict[Metric, Any] = {
            fundamental_metrics_by_yahoo_name[yahoo_metric_name]: value
            for yahoo_metric_name, value in fundamental_metrics_values.items()
        }
        for metric in metrics:
            if metric in (Metric.RETURN_ON_EQUITY, Metric.DIVIDEND_PAYOUT_RATIO):
                fraction_value = fundamenal_metrics[metric]
                if fraction_value is not None:
                    fundamenal_metrics[metric] = Percentage(fraction_value)
            elif metric.label.endswith("%"):
                percent_value = fundamenal_metrics[metric]
                if percent_value is not None:
                    fundamenal_metrics[metric] = Percentage(percent_value / 100)
        return fundamenal_metrics
    combined_metrics: dict[Metric,Any] = fetch_fundamental_metrics()
    if Metric.PRICE in metrics:
        try:
            combined_metrics[Metric.PRICE] = fetch_price(company_id)
        except Exception as e:
            combined_metrics[Metric.PRICE] = e
    if Metric.PRICE_IN_EURO in metrics:
        existing_price = combined_metrics.get(Metric.PRICE)
        if not isinstance(existing_price, Price):
            existing_price = None
        try:
            combined_metrics[Metric.PRICE_IN_EURO] = fetch_price_in_euro(
                company_id=company_id, existing_price=existing_price
            )
        except Exception as e:
            combined_metrics[Metric.PRICE_IN_EURO] = e
    return MetricsRecord(company_id=company_id, metrics=MappingProxyType(combined_metrics))

def fetch_current_metrics_batch(
        company_ids: Collection[str], metrics: Collection[Metric], thread_amount: int | None
) -> tuple[list[MetricsRecord], list[MetricsRecord]]:
    """Fetch metrics for ``company_ids``, split into records without errors and
    records with errors.

    Returns a ``(records_without_errors, records_with_errors)`` tuple.
    """
    if thread_amount is not None:
        company_ids = list(company_ids)
        if not company_ids:
            return [], []
        with ThreadPoolExecutor(max_workers=min(len(company_ids), thread_amount)) as executor:
            records = list(
                executor.map(
                    lambda company_id: fetch_current_metrics(company_id, metrics), company_ids
                )
            )
    else:
        records = [fetch_current_metrics(company_id, metrics) for company_id in company_ids]

    records_without_errors = [record for record in records if not record.has_errors()]
    records_with_errors = [record for record in records if record.has_errors()]
    return records_without_errors, records_with_errors
