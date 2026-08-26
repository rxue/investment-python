import logging
import math
from collections.abc import Mapping
from enum import Enum
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)

class Metric(Enum):
    COMPANY_NAME = ("shortName", "Company Name")
    PRICE = (None, "Price")
    PRICE_IN_EURO = (None, "Price in EURO")
    MARKET_STATE = ("marketState", "Market State")
    TRAILING_PE = ("trailingPE", "Trailing P/E")
    DIVIDEND_YIELD = ("dividendYield", "Dividend Yield %")
    DIVIDEND_PAYOUT_RATIO = ("payoutRatio", "Dividend Payout Ratio %")
    RETURN_ON_EQUITY = ("returnOnEquity", "Return on Equity %")
    REGULAR_MARKET_CHANGE_PERCENT = ("regularMarketChangePercent", "Regular Market Change %")
    PRICE_TO_BOOK = ("priceToBook", "Price to Book")

    def __init__(self, yahoo_metric_name: str | None, label: str) -> None:
        self.yahoo_metric_name = yahoo_metric_name
        self.label = label


class MetricsRecord(NamedTuple):
    company_id: str
    metrics: Mapping[Metric, Any]
    def to_readable(self) -> dict[str,Any]:
        result:dict[str,Any] = {"company":self.company_id}
        logger.info(f"Company: {self.company_id}")
        for metric,value in self.metrics.items():
            if metric == Metric.PRICE:
                result[metric.label] = value.value_with_currency()
            elif metric == Metric.PRICE_IN_EURO:
                result[metric.label] = value.amount()
            elif metric.label.endswith("%") and value is not None:
                logger.info(f"Metric, {metric}, with percent or fraction value: {value}")
                result[metric.label] = value.percent_value()
            elif metric == Metric.TRAILING_PE:
                if value is not None:
                    result[metric.label] = int(value*10)/10
            elif metric == Metric.PRICE_TO_BOOK:
                if value is not None:
                    result[metric.label] = int(value*100)/100
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
