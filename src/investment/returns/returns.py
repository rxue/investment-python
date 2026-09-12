from datetime import date
from typing import NamedTuple

from investment.vo.value_objects import IndexSeries


class DailyReturnSeries(NamedTuple):
    value_by_date:dict[date,float]
    def to_index_series(self,label:str) -> IndexSeries:
        """Compound this series' daily returns into a rebased index series,
        starting from 100 and multiplying by ``(1 + daily_return)`` for each
        date in turn."""
        value_by_date: dict[date, float] = {}
        cumulative_return = 100.0
        for return_date, daily_return in self.value_by_date.items():
            cumulative_return *= 1 + daily_return
            value_by_date[return_date] = cumulative_return
        return IndexSeries(label=label, value_by_date=value_by_date)
