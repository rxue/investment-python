"""Orchestration for the CLI ``metrics`` command."""

import logging
import time
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd

from investment.benchmark.chart_data import ChartData
from investment.marketquote import metrics, repository
from investment.marketquote.filter import Range, records_out_of_range
from investment.util.decorator import clock
from investment.vo.value_objects import Period

logger = logging.getLogger(__name__)


@clock
def _run_metrics(
    names: str,
    company_symbols: str | None = None,
    company_csv: str | None = None,
    sort_by: str | None = None,
    price_ranges_str: str | None = None,
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

    def _load_company_symbols(csv_source: str) -> str:
        """Load comma-delimited Yahoo ticker symbols from a company CSV file.

        ``csv_source`` may be a local file path or an http(s) URL. The CSV must
        contain a "Yahoo Company Symbol" column, e.g.
        https://gist.githubusercontent.com/rxue/7ec0914a8af1525d97e8dfd2ac5d61d7/raw/companies.csv
        """
        companies = pd.read_csv(csv_source)
        return ",".join(companies["Yahoo Company Symbol"].astype(str))

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

    if company_symbols:
        company_ids = company_symbols
    elif company_csv is not None:
        company_ids = _load_company_symbols(company_csv)
    else:
        raise SystemExit(
            "investment metrics: error: one of --company-symbols or --company-csv is required"
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
        pd.DataFrame([r.company_id for r in erratic_rows], columns=["non-existing company"]),
        records_out_of_range_df,
    )

def _run_benchmark(benchmark_id:str,company_id:str,start_date:str,end_date:str) -> ChartData:
    period = Period(from_date=date.fromisoformat(start_date), to_date=date.fromisoformat(end_date))
    return ChartData.generate(benchmark_id, company_id, period)

def _generate_benchmark_chart(
    chart_data:ChartData, output_path:str|None=None, show:bool=True
) -> str|None:
    """Plot the benchmark's and stock's rebased index series.

    Displays the chart in a window by default (``show=True``). Saved to
    ``output_path`` only if given; returns that path, or ``None`` if not saved.
    """
    benchmark_index = chart_data.benchmark_index()
    stock_index = chart_data.stock_index()

    fig, ax = plt.subplots()
    ax.plot(
        benchmark_index.index_series.index.to_numpy(), benchmark_index.index_series.to_numpy(),
        label=benchmark_index.symbol,
    )
    ax.plot(
        stock_index.index_series.index.to_numpy(), stock_index.index_series.to_numpy(),
        label=stock_index.symbol,
    )
    ax.axhline(chart_data.base, color="gray", linestyle="--", linewidth=0.8)
    ax.set_title(
        f"{stock_index.symbol} vs {benchmark_index.symbol} — indexed to {chart_data.base:.0f}"
    )
    ax.set_ylabel("Index value")
    ax.legend()
    fig.autofmt_xdate()

    if output_path is not None:
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)
    return output_path
