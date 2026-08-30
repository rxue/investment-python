"""Integration tests for ``repository.fetch_price_in_euro``,
``repository.fetch_current_metrics``, and ``repository.fetch_historical_prices``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
from datetime import date, timedelta

import pytest

from investment.marketquote.metrics import Metric
from investment.marketquote.repository import (
    fetch_current_metrics,
    fetch_historical_prices,
    fetch_price,
    fetch_price_in_euro,
)
from investment.vo.value_objects import Period

pytestmark = pytest.mark.integration


def test_fetch_price_in_euro_converts_non_eur_price():
    """A USD-quoted symbol should get a distinct, positive EUR conversion."""
    price_in_euro = fetch_price_in_euro("AAPL")

    assert price_in_euro.currency_value() == "EUR"
    assert price_in_euro.amount() > 0
    assert (date.today() - price_in_euro.timestamp.date()).days <= 3


def test_fetch_price_in_euro_passthrough_for_eur_symbol():
    """A symbol already quoted in EUR should convert to the same amount."""
    price = fetch_price("ELISA.HE")
    assert price.amount() > 0
    price_in_euro = fetch_price_in_euro("ELISA.HE", existing_price=price)

    assert price.currency_value() == "EUR"
    assert price_in_euro.currency_value() == "EUR"
    assert price_in_euro.amount() == price.amount()
    assert (date.today() - price_in_euro.timestamp.date()).days <= 3


def test_fetch_current_metrics_when_company_does_not_exist_thus_has_no_price():
    """A symbol that doesn't exist on Yahoo Finance has no quoted price to
    return, so fetching ``Metric.PRICE`` for it should raise, not silently
    produce a record with a missing price.
    """
    metric_record = fetch_current_metrics("NOTHING", [Metric.PRICE,Metric.PRICE_IN_EURO])
    assert metric_record.has_errors() is True


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
    assert price_series.prices
    assert len(price_series) > 2
    for trading_date, price in price_series.prices.items():
        assert start <= trading_date <= end
        assert price > 0
