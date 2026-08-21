"""Integration tests for ``repository.fetch_price_in_euro``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
from datetime import date

import pytest

from investment.marketquote.repository import fetch_price, fetch_price_in_euro

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
