"""Integration tests for ``repository.fetch_current_metrics``,
``repository.fetch_fx_rate_series_from_euro``, and ``repository.fetch_historical_prices``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
from datetime import date, timedelta
from typing import Final

import pytest

from investment.marketquote.metrics import Metric
from investment.marketquote.repository import (
    fetch_current_metrics,
    fetch_fx_rate_series_from_euro,
    fetch_historical_prices,
)
from investment.vo.value_objects import Period

pytestmark = pytest.mark.integration


def test_fetch_current_metrics_when_company_does_not_exist_thus_has_no_price():
    """A symbol that doesn't exist on Yahoo Finance has no quoted price to
    return, so fetching ``Metric.PRICE`` for it should raise, not silently
    produce a record with a missing price.
    """
    metric_record = fetch_current_metrics("NOTHING", [Metric.PRICE,Metric.PRICE_IN_EURO])
    assert metric_record.has_errors() is True


def test_fetch_fx_rate_series_from_euro_returns_daily_rates_for_period():
    """A period spanning the Christmas break should come back as an
    EUR-to-USD series whose dates all fall within the requested period and
    whose rates are all positive - with no entry for the holidays/weekend
    the ECB doesn't publish a rate for.
    """
    period = Period(from_date=date(2025, 12, 22), to_date=date(2025, 12, 30))

    fx_rate_series = fetch_fx_rate_series_from_euro("USD", period)

    assert fx_rate_series.base_currency == "EUR"
    assert fx_rate_series.quote_currency == "USD"
    assert fx_rate_series.values
    for trading_date, rate in fx_rate_series.values.items():
        assert period.from_date <= trading_date <= period.to_date
        assert rate > 0


def test_fetch_historical_prices_returns_daily_close_series_for_period():
    """A recent, deliberately-short period should come back as a currency
    plus a non-empty ``{date: price}`` series whose dates all fall within
    the requested period and whose prices are all positive.
    """
    end = date.today()
    start = end - timedelta(days=10)
    period = Period(from_date=start, to_date=end)

    price_series = fetch_historical_prices("AAPL", period)

    assert price_series.currency == "USD"
    cent_prices:Final = price_series.cent_prices
    assert cent_prices
    assert len(cent_prices) > 2
    for trading_date, cent_price in cent_prices.items():
        assert start <= trading_date <= end
        assert cent_price > 0
