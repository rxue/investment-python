from datetime import date
from typing import NamedTuple

from investment.vo.value_objects import IndexSeries


class DailyReturnSeries(NamedTuple):
    value_by_date:dict[date,float]
    def to_index_series(self, base:float=100) -> IndexSeries:
        """Compound this series' daily returns into a rebased index series.

        Starts from ``base`` (before the first date in ``value_by_date``)
        and multiplies by ``(1 + daily_return)`` for each date in turn, so
        the result is directly comparable to a price-based index series
        (e.g. ``ChartData``'s benchmark/stock indices) rebased to the same
        ``base``.

        ``value_by_date`` MUST already be ordered by date, ascending - this
        is a precondition the caller is responsible for, not something this
        method checks or sorts for you, since the running value is compounded
        strictly in dict-iteration order.
        """
        value_by_date: dict[date, float] = {}
        running_value = base
        for return_date, daily_return in self.value_by_date.items():
            running_value *= 1 + daily_return
            value_by_date[return_date] = running_value
        return IndexSeries(value_by_date=value_by_date)
