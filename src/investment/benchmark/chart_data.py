from typing import NamedTuple

import pandas as pd

from investment.marketquote.repository import fetch_historical_prices
from investment.vo.value_objects import Period, PriceSeries


class LabeledIndexSeries(NamedTuple):
    symbol: str
    index_series: pd.Series

class ChartData(NamedTuple):
    benchmark: tuple[str,PriceSeries]
    stock: tuple[str,PriceSeries]
    base:float=100


    def _to_index(self, price_series:PriceSeries) -> pd.Series:
        prices = pd.Series(price_series.cent_prices).sort_index()
        return prices / prices.iloc[0] * self.base

    def benchmark_index(self) -> LabeledIndexSeries:
        """Return the benchmark's price series rebased to ``base`` at its first date."""
        benchmark_id = self.benchmark[0]
        price_series = self.benchmark[1]
        return LabeledIndexSeries(benchmark_id, self._to_index(price_series))

    def stock_index(self) -> LabeledIndexSeries:
        """Return the stock's price series rebased to ``base`` at its first date."""
        company_id = self.stock[0]
        price_series = self.stock[1]
        return LabeledIndexSeries(company_id, self._to_index(price_series))

    def coefficient(self)->float:
        """Return the stock's beta relative to the benchmark over the period.

        Beta = Cov(stock returns, benchmark returns) / Var(benchmark returns),
        computed from daily returns of the raw price series.
        """
        benchmark_prices = pd.Series(self.benchmark[1].cent_prices).sort_index()
        stock_prices = pd.Series(self.stock[1].cent_prices).sort_index()
        benchmark_returns = benchmark_prices.pct_change().dropna()
        stock_returns = stock_prices.pct_change().dropna()
        aligned = pd.concat(
            [benchmark_returns, stock_returns], axis=1, join="inner", keys=["benchmark", "stock"]
        )
        covariance = aligned["stock"].cov(aligned["benchmark"])
        variance = aligned["benchmark"].var()
        return covariance / variance

    @staticmethod
    def generate(benchmark_id:str, company_id:str, period:Period) -> "ChartData":
        benchmark_price_series = fetch_historical_prices(benchmark_id, period)
        stock_price_series = fetch_historical_prices(company_id, period)
        return ChartData((benchmark_id, benchmark_price_series), (company_id, stock_price_series))
