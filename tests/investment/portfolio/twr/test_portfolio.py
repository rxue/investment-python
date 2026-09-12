"""Unit tests for ``investment.portfolio.twr.portfolio.Holding``."""
import pytest

from investment.portfolio.twr.portfolio import Holding


def test_market_value_in_cent_with_no_price_raises_value_error():
    """A ``Holding`` built with only ``position`` (no ``price_in_cent``)
    defaults its price to ``None``. Calling ``market_value_in_cent`` on such
    an unpriced holding is a misuse - it can't produce a market value - so
    it should raise a clear ``ValueError`` rather than blow up with a
    confusing ``TypeError`` from the underlying multiplication.
    """
    holding = Holding(10)

    with pytest.raises(ValueError, match="requires a priced Holding"):
        holding.market_value_in_cent()
