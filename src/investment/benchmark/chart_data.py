import itertools
import statistics
from datetime import date
from typing import NamedTuple

from investment.marketquote.repository import fetch_historical_prices
from investment.vo.value_objects import Period, PriceSeries

class LabeledIndexSeries(NamedTuple):
    symbol: str
    index_series: dict[date, float]

class ChartData(NamedTuple):
    benchmark: tuple[str,PriceSeries]
    stock: tuple[str,PriceSeries]
    base:float=100


    def _to_index(self, price_series:PriceSeries) -> tuple[date,float]:
        first_price:int = next(iter(price_series.cent_prices.values()))
        return {date:price/first_price*100 for date,price in price_series.cent_prices.items()}

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
        computed from daily returns over the trading dates common to both series.
        """
        benchmark_prices = self.benchmark[1].cent_prices
        stock_prices = self.stock[1].cent_prices
        common_dates = sorted(benchmark_prices.keys() & stock_prices.keys())
        if len(common_dates) < 2:
            raise ValueError(
                "Not enough overlapping trading dates between benchmark and stock to compute a beta"
            )

        benchmark_returns = [
            benchmark_prices[curr] / benchmark_prices[prev] - 1
            for prev, curr in itertools.pairwise(common_dates)
        ]
        stock_returns = [
            stock_prices[curr] / stock_prices[prev] - 1
            for prev, curr in itertools.pairwise(common_dates)
        ]

        benchmark_variance = statistics.variance(benchmark_returns)
        if benchmark_variance == 0:
            raise ValueError("Benchmark returns have zero variance; beta is undefined")

        return statistics.covariance(stock_returns, benchmark_returns) / benchmark_variance

    @staticmethod
    def generate(benchmark_id:str, company_id:str, period:Period) -> "ChartData":
        benchmark_price_series = fetch_historical_prices(benchmark_id, period)
        stock_price_series = fetch_historical_prices(company_id, period)
        return ChartData((benchmark_id, benchmark_price_series), (company_id, stock_price_series))
