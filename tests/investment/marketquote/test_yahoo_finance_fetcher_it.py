"""Integration tests for ``yahoo_finance_fetcher.fetch_fundamental_metrics``.

These hit the real Yahoo Finance API over the network (no mocking) - hence
"IT" rather than a unit test.
"""
import pytest

from investment.marketquote.yahoo_finance_fetcher import fetch_fundamental_metrics

pytestmark = pytest.mark.integration


def test_fetch_fundamental_metrics_unknown_symbol_returns_none_values():
    """LEARNING TEST: A symbol that doesn't exist on Yahoo Finance should surface every
    requested metric as ``None`` rather than raising or being omitted.
    """
    result = fetch_fundamental_metrics("NOTHING", ["trailingPE", "xxx"])

    assert result == {"trailingPE": None, "xxx": None}
