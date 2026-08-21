import math
from enum import Enum
from typing import Any, NamedTuple


class Metric(Enum):
    COMPANY_NAME = ("shortName", "Company Name")
    PRICE = (None, "Price")
    PRICE_IN_EURO = (None, "Price in EURO")
    TRAILING_PE = ("trailingPE", "Trailing P/E")
    DIVIDEND_YIELD = ("dividendYield", "Dividend Yield")
    RETURN_ON_EQUITY = ("returnOnEquity", "Return on Equity")
    REGULAR_MARKET_CHANGE_PERCENT = ("regularMarketChangePercent", "Regular Market Change %")
    PRICE_TO_BOOK = ("priceToBook", "Price to Book")

    def __init__(self, yahoo_metric_name: str | None, label: str) -> None:
        self.yahoo_metric_name = yahoo_metric_name
        self.label = label


class MetricsRecord(NamedTuple):
    company_id: str
    metrics: dict[Metric, Any]
    def to_readable(self) -> dict[str,Any]:
        result = {"company":self.company_id}
        for metric,value in self.metrics.items():
            if metric == Metric.PRICE:
                result[metric.label] = value.value_with_currency()
            elif metric == Metric.PRICE_IN_EURO:
                result[metric.label] = value.amount()
            else:
                result[metric.label] = value
        return result

def sort_records(records: list[MetricsRecord], sort_by: Metric) -> list[MetricsRecord]:
    """Sort ``records`` by their ``sort_by`` metric value, ascending.

    Records missing ``sort_by`` (absent key, ``None``, or ``NaN``) sort last,
    regardless of the metric's type.
    """
    def sort_key(record: MetricsRecord) -> tuple[bool, Any]:
        value = record.metrics.get(sort_by)
        if sort_by in (Metric.PRICE, Metric.PRICE_IN_EURO) and value is not None:
            value = value.amount()
        is_missing = value is None or (isinstance(value, float) and math.isnan(value))
        return (is_missing, 0.0 if is_missing else value)

    return sorted(records, key=sort_key)
