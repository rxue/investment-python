import itertools
import statistics
from typing import NamedTuple

from investment.benchmark._index import get_benchmark_index_series, get_stock_index_series
from investment.portfolio.transaction import Transaction, get_period
from investment.portfolio.twr.calculation import calculate_twr
from investment.vo.value_objects import IndexSeries, Period


class BenchmarkResult(NamedTuple):
    benchmark_series:IndexSeries
    subject_series:IndexSeries
    def _paired_returns(self) -> tuple[list[float],list[float]]:
        """Return ``(benchmark_returns, subject_returns)`` - day-over-day
        percentage changes derived from each series' rebased index levels
        (equivalent to deriving them from raw prices, since rebasing is a
        linear transform) - over the trading dates common to both series."""
        benchmark_values = self.benchmark_series.value_by_date
        subject_values = self.subject_series.value_by_date
        common_dates = sorted(benchmark_values.keys() & subject_values.keys())
        if len(common_dates) < 2:
            raise ValueError(
                "Not enough overlapping trading dates between benchmark and "
                "subject to compute a beta or correlation"
            )

        benchmark_returns = [
            benchmark_values[curr] / benchmark_values[prev] - 1
            for prev, curr in itertools.pairwise(common_dates)
        ]
        subject_returns = [
            subject_values[curr] / subject_values[prev] - 1
            for prev, curr in itertools.pairwise(common_dates)
        ]
        return benchmark_returns, subject_returns

    def coefficient(self) -> float:
        """Return the subject's beta relative to the benchmark over the period.

        Beta = Cov(subject returns, benchmark returns) / Var(benchmark returns).
        Unlike ``correlation_coefficient()``, beta is unbounded - it measures
        how much the subject amplifies or dampens the benchmark's moves, not
        how tightly the two move together.
        """
        benchmark_returns, subject_returns = self._paired_returns()
        benchmark_variance = statistics.variance(benchmark_returns)
        if benchmark_variance == 0:
            raise ValueError("Benchmark returns have zero variance; beta is undefined")

        return statistics.covariance(subject_returns, benchmark_returns) / benchmark_variance

    def correlation_coefficient(self) -> float:
        """Return the Pearson correlation coefficient between the subject's
        and the benchmark's daily returns over the period.

        Bounded to [-1, 1], unlike ``coefficient()`` (beta), which has no
        such bound - this measures how tightly the two move together, not
        by how much.
        """
        benchmark_returns, subject_returns = self._paired_returns()
        return statistics.correlation(subject_returns, benchmark_returns)

    @staticmethod
    def benchmark_security(benchmark_id:str,security_id:str,period:Period) -> "BenchmarkResult":
        benchmark_currency,benchmark_price_series = get_benchmark_index_series(benchmark_id,period)
        stock_price_series = get_stock_index_series(security_id,period,benchmark_currency)
        return BenchmarkResult(benchmark_price_series, stock_price_series)
    @staticmethod
    def benchmark_portfolio(
        benchmark_id:str,portfolio_transactions:list[Transaction]
    ) -> "BenchmarkResult":
        period:Period = get_period(portfolio_transactions)
        benchmark_currency,benchmark_index_series = get_benchmark_index_series(benchmark_id,period)
        _,portfolio_daily_return_series = calculate_twr(portfolio_transactions,benchmark_currency)
        subject_series = portfolio_daily_return_series.to_index_series("Your Portfolio")
        return BenchmarkResult(benchmark_index_series, subject_series)

