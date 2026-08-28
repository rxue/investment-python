"""Orchestration for the CLI ``metrics`` command."""

import logging
import time

import pandas as pd

from investment.marketquote import metrics, repository
from investment.marketquote.filter import Range, records_out_of_range
from investment.util.decorator import clock

logger = logging.getLogger(__name__)


@clock
def _run_metrics(
    names: str, company_ids: str, sort_by: str | None = None, price_ranges_str: str | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def extract_price_ranges() -> dict[str, Range]:
        if not price_ranges_str:
            return {}
        result: dict[str, Range] = {}
        for entry in price_ranges_str.split(","):
            company_id, start, end = entry.split(":")
            result[company_id] = Range(
                start=float(start) if start else None,
                end=float(end) if end else None,
            )
        return result

    metric_names = [name.strip() for name in names.split(",")]
    try:
        metric_list = [repository.Metric[name] for name in metric_names]
    except KeyError as exc:
        valid_names = ", ".join(metric.name for metric in repository.Metric)
        raise SystemExit(
            f"investment metrics: error: argument --names: invalid choice: {exc.args[0]!r} "
            f"(choose from {valid_names})"
        ) from None

    sort_by_metric = None
    if sort_by is not None:
        try:
            sort_by_metric = repository.Metric[sort_by]
        except KeyError:
            valid_names = ", ".join(metric.name for metric in repository.Metric)
            raise SystemExit(
                f"investment metrics: error: argument --sort-by: invalid choice: {sort_by!r} "
                f"(choose from {valid_names})"
            ) from None
        if sort_by_metric not in metric_list:
            raise SystemExit(
                f"investment metrics: error: argument --sort-by: {sort_by!r} must be one of the "
                f"metrics in --names ({', '.join(metric_names)})"
            )

    company_id_list = [symbol.strip() for symbol in company_ids.split(",")]
    batch_size = 100
    thread_amount = 10
    if len(company_id_list) > batch_size:
        rows = []
        erratic_rows = []
        for i in range(0, len(company_id_list), batch_size):
            batch = company_id_list[i : i + batch_size]
            metrics_records, erratic_metrics_records = repository.fetch_current_metrics_batch(
                batch, metric_list, thread_amount
            )
            rows.extend(metrics_records)
            erratic_metrics_records.extend(erratic_metrics_records)
            logger.info("Executed one batch")
            time.sleep(60)
    else:
        rows, erratic_rows = repository.fetch_current_metrics_batch(
            company_id_list, metric_list, thread_amount
        )

    if sort_by_metric is not None:
        rows = metrics.sort_records(rows, sort_by_metric)
    records_out_of_range_df = pd.DataFrame()
    if price_ranges_str is not None:
        price_ranges = extract_price_ranges()
        records_outside = records_out_of_range(rows, price_ranges)
        records_out_of_range_df = pd.DataFrame([r.to_readable() for r in records_outside])
    return (
        pd.DataFrame([r.to_readable() for r in rows]),
        pd.DataFrame([r.company_id for r in erratic_rows]),
        records_out_of_range_df,
    )
