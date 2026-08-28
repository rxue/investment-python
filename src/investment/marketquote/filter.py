import math
from typing import NamedTuple

from investment.marketquote.metrics import Metric, MetricsRecord


class Range(NamedTuple):
    start: float | None
    end: float | None
    def has(self, value:float) -> bool:
        start = self.start if self.start else 0
        end = self.end if self.end else math.inf
        return start <= value <= end

def records_out_of_range(
    all_metric_records: list[MetricsRecord], ranges: dict[str, Range]
) -> list[MetricsRecord]:
    """Return the records whose ``Metric.PRICE`` falls outside its configured range.

    A record is skipped (not returned) when its company has no configured
    range, no ``Metric.PRICE`` value, or that value is an error rather than a
    ``Price``.
    """
    result = []
    for record in all_metric_records:
        price_range = ranges.get(record.company_id)
        if price_range is None:
            continue
        price = record.metrics.get(Metric.PRICE)
        if price is None or isinstance(price, Exception):
            continue
        if not price_range.has(price.amount()):
            result.append(record)
    return result
