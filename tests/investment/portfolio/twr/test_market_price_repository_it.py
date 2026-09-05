"""Integration tests for
``_market_price_repository.find_historical_price_series``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
from datetime import date

import pytest

from investment.marketquote._fx_rate_fetcher import fetch_fx_rate_from_euro
from investment.marketquote.repository import fetch_historical_prices
from investment.portfolio.twr._market_price_repository import (
    _find_historical_euro_price_series,
)
from investment.vo.value_objects import Period

pytestmark = pytest.mark.integration

FIRST_WEEK_OF_2026 = Period(from_date=date(2026, 1, 1), to_date=date(2026, 1, 7))


def test_find_historical_price_series_converts_usd_prices_for_period():
    """PFE is USD-quoted, so the returned series should be a non-empty,
    positive EUR-cent series whose dates all fall within the requested
    first week of 2026.
    """
    euro_price_series = _find_historical_euro_price_series("PFE", FIRST_WEEK_OF_2026)

    assert euro_price_series.currency == "EUR"
    assert euro_price_series.cent_prices
    for trading_date, cent_price in euro_price_series.cent_prices.items():
        assert FIRST_WEEK_OF_2026.from_date <= trading_date <= FIRST_WEEK_OF_2026.to_date
        assert cent_price > 0


def test_find_historical_price_series_matches_usd_price_times_fx_rate():
    """Each day's EUR-cent value should equal that day's USD-cent close
    converted through that same day's ECB USD-to-EUR rate, not a single
    blanket rate for the whole period.
    """
    usd_price_series = fetch_historical_prices("PFE", FIRST_WEEK_OF_2026)
    euro_price_series = _find_historical_euro_price_series("PFE", FIRST_WEEK_OF_2026)

    assert usd_price_series.cent_prices.keys() == euro_price_series.cent_prices.keys()
    for trading_date, usd_cent_price in usd_price_series.cent_prices.items():
        _, fx_rate = fetch_fx_rate_from_euro("USD", trading_date)
        expected_euro_cent_price = round(usd_cent_price / fx_rate)
        assert euro_price_series.cent_prices[trading_date] == expected_euro_cent_price
