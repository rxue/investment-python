"""Unit tests for ``investment.benchmark.index._get_index_series`` (mocked, no network)."""
from datetime import date
from typing import Final
from unittest.mock import patch

from investment.benchmark.index import _get_index_series
from investment.vo.value_objects import Period, PriceSeries


@patch("investment.benchmark.index.fetch_historical_prices")
def test_get_index_series_converts_to_given_currency(mock_fetch_historical_prices):
    """``_get_index_series`` should pass ``currency`` straight through to
    ``fetch_historical_prices`` and rebase whatever price series comes back
    to 100 at its first date, regardless of what currency it's quoted in.
    """
    inclusive_start_date:Final = date(2026, 2, 5)
    inclusive_end_date = date(2026, 2, 6)
    period = Period(from_date=inclusive_start_date, to_date=inclusive_end_date)
    mock_fetch_historical_prices.return_value = PriceSeries(
        currency="USD",
        cent_prices={
            inclusive_start_date: 25791,
            inclusive_end_date: 27737,
        },
    )

    currency, index_series = _get_index_series("AAPL", period, currency="DKK")

    mock_fetch_historical_prices.assert_called_once_with("AAPL", period, currency="DKK")
    assert currency == "DKK"

@patch("investment.benchmark.index.fetch_historical_prices")
def test_get_index_series_with_original_currency(mock_fetch_historical_prices):
    """``_get_index_series`` should pass ``currency`` straight through to
    ``fetch_historical_prices`` and rebase whatever price series comes back
    to 100 at its first date, regardless of what currency it's quoted in.
    """
    inclusive_start_date:Final = date(2026, 2, 5)
    inclusive_end_date = date(2026, 2, 6)
    period = Period(from_date=inclusive_start_date, to_date=inclusive_end_date)
    mock_fetch_historical_prices.return_value = PriceSeries(
        currency="USD",
        cent_prices={
            inclusive_start_date: 25791,
            inclusive_end_date: 27737,
        },
    )

    currency, index_series = _get_index_series("AAPL", period, currency=None)
    mock_fetch_historical_prices.assert_called_once_with("AAPL", period, currency=None)
    assert currency == "USD"
