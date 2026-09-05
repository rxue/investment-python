"""Unit tests for ``value_objects.PriceSeries`` and ``value_objects.FxRateSeries``."""
from datetime import date, timedelta
from decimal import Decimal

from investment.vo.value_objects import FxRateSeries, PriceSeries


def test_get_price_returns_the_price_on_the_requested_date():
    """A date present in the series should come back as a ``Price`` with
    that date's cent value and the series' currency.
    """
    trading_date = date(2026, 1, 2)
    price_series = PriceSeries(
        currency="USD",
        cent_prices={trading_date: 12345, date(2026, 1, 5): 12400},
    )

    price = price_series.get_price(trading_date)

    assert price.cent_value == 12345
    assert price.currency == "USD"
    assert price.date() == trading_date


def test_get_price_on_a_weekend_falls_back_to_friday():
    """A Saturday has no trading price, so ``get_price`` should walk
    backwards to the preceding Friday.
    """
    friday = date(2026, 1, 2)
    price_series = PriceSeries(
        currency="USD",
        cent_prices={friday: 12345},
    )

    price = price_series.get_price(friday + timedelta(days=1))

    assert price.cent_value == 12345
    assert price.date() == friday


def test_get_price_on_a_weekend_skips_a_missing_friday():
    """If Friday itself has no price either (e.g. a holiday), ``get_price``
    should keep walking backwards until it finds one.
    """
    thursday = date(2026, 1, 1)
    sunday = date(2026, 1, 4)
    price_series = PriceSeries(
        currency="USD",
        cent_prices={thursday: 12000},
    )

    price = price_series.get_price(sunday)

    assert price.cent_value == 12000
    assert price.date() == thursday


def test_get_falls_back_to_the_last_published_rate():
    """Only 2025-12-24 (the start) and 2025-12-29 (the end) have a published
    rate - the Christmas holidays/weekend in between don't - so ``get``
    should return each date's own rate when present, and otherwise fall
    back to the most recent earlier published date.
    """
    fx_rate_series = FxRateSeries(
        base_currency="EUR",
        quote_currency="USD",
        values={
            date(2025, 12, 24): Decimal("1.1787"),
            date(2025, 12, 29): Decimal("1.1766"),
        },
    )

    assert fx_rate_series.get(date(2025, 12, 24)) == Decimal("1.1787")
    assert fx_rate_series.get(date(2025, 12, 26)) == Decimal("1.1787")
    assert fx_rate_series.get(date(2025, 12, 29)) == Decimal("1.1766")
