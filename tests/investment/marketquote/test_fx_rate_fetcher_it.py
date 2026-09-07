"""Integration tests for ``_fx_rate_fetcher.fetch_fx_rate_series_from_euro``.

These hit the real ECB Data Portal API over the network (no mocking) - hence
"IT" rather than a unit test.
"""
from datetime import date
from decimal import Decimal

import pytest

from investment.marketquote._fx_rate_fetcher import fetch_fx_rate_series_from_euro
from investment.util.util import EUR

pytestmark = pytest.mark.integration


def test_fetch_fx_rate_series_from_euro_with_euro_is_identity():
    """EUR-to-EUR should short-circuit to a 1:1 rate for every day in the
    range unchanged, without needing to hit the ECB API at all.
    """
    result = fetch_fx_rate_series_from_euro(EUR, date(2026, 1, 1), date(2026, 1, 2))

    assert result == [
        (date(2026, 1, 1), Decimal(1)),
        (date(2026, 1, 2), Decimal(1)),
    ]
