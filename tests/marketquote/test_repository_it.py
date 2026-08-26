"""Integration tests for ``repository.fetch_price_in_euro`` and
``repository.fetch_current_metrics``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
from datetime import date

import pytest

from investment.marketquote.metrics import Metric
from investment.marketquote.repository import (
    fetch_current_metrics,
    fetch_price,
    fetch_price_in_euro,
)

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
