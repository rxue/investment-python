"""Unit tests for ``metrics.MetricsRecord``."""
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
