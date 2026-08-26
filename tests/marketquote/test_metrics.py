"""Unit tests for ``metrics.MetricsRecord``."""
import pytest

from investment.marketquote.metrics import Metric, MetricsRecord


def test_has_errors_true_when_a_metric_value_is_an_exception():
    """A metrics dict holding an exception instance (e.g. a failed fetch)
    should be reported as containing errors.
    """
    record = MetricsRecord(
        company_id="AAPL", metrics={Metric.PRICE: ValueError("could not fetch price")}
    )

    assert record.has_errors() is True

def test_has_errors_false():
    """A metrics dict holding an exception instance (e.g. a failed fetch)
    should be reported as containing errors.
    """
    record = MetricsRecord(
        company_id="AAPL", metrics={Metric.TRAILING_PE: 15.1}
    )

    assert record.has_errors() is False

def test_to_readable_when_there_is_error():
    """In case there is error in the MetricRecord, to_readable should throw ValueError with explict explanation message
    """
    record = MetricsRecord(
        company_id="AAPL", metrics={Metric.PRICE: ValueError("could not fetch price")}
    )

    with pytest.raises(ValueError) as exc_info:
        record.to_readable()

    assert "AAPL" in str(exc_info.value)
    assert "Price" in str(exc_info.value)
    assert "could not fetch price" in str(exc_info.value)
