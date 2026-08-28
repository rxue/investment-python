"""Unit tests for ``price_alert.Range``."""
from investment.alert.price_alert import Range


def test_has_true_when_value_is_within_range():
    range_ = Range(start=32, end=40)

    assert range_.has(33) is True
