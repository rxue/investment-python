"""Unit tests for ``repository.fetch_current_metrics`` (mocked, no network)."""
from unittest.mock import patch

from investment.marketquote.metrics import Metric
from investment.marketquote.repository import fetch_current_metrics


@patch("investment.marketquote.yahoo_finance_fetcher.fetch_fundamental_metrics")
def test_fetch_current_metrics_return_on_equity_none(mock_fetch_fundamental_metrics):
    """A company with no reported ROE (e.g. negative equity) should surface as
    a missing metric, not crash or silently wrap ``None`` in a ``Percentage``.
    """
    mock_fetch_fundamental_metrics.return_value = {"returnOnEquity": None}

    record = fetch_current_metrics("MO", [Metric.RETURN_ON_EQUITY])

    mock_fetch_fundamental_metrics.assert_called_once_with("MO", {"returnOnEquity"})
    assert record.company_id == "MO"
    assert record.metrics[Metric.RETURN_ON_EQUITY] is None
