"""Command-line entry point for the investment toolkit.

Usage examples::

    investment-python price AAPL
    investment-python price AAPL --date 2026-08-01
    investment-python metrics PRICE,TRAILING_PE --company-symbols AAPL
"""
import argparse
import logging
import os
import sys
from enum import StrEnum
from typing import Sequence

from investment.cli.program_runner import _generate_benchmark_chart, _run_benchmark, _run_metrics
from investment.marketquote import repository


class Command(StrEnum):
    METRICS = "metrics"
    BENCHMARK = "benchmark"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment", description="Fetch market quotes and fundamentals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    def _build_metrics_parser() -> None:
        metrics_parser = subparsers.add_parser(
            Command.METRICS, help="Fetch metrics for symbols."
        )
        metrics_parser.add_argument(
            "metric_names",
            help="One or more metrics to fetch, delimited by comma, e.g. PRICE,TRAILING_PE. "
            f"Choose from {', '.join(metric.name for metric in repository.Metric)}.",
        )
        company_source_group = metrics_parser.add_mutually_exclusive_group(required=True)
        company_source_group.add_argument(
            "--company-symbols",
            help="Company ticker symbols delimited by comma, e.g. AAPL,ELISA.HE",
        )
        company_source_group.add_argument(
            "--company-csv",
            help="Path or URL to a company CSV file with a 'Yahoo Company Symbol' column, "
            "e.g. https://gist.githubusercontent.com/rxue/7ec0914a8af1525d97e8dfd2ac5d61d7/raw/companies.csv",
        )
        metrics_parser.add_argument(
            "--sort-by",
            default=None,
            help="Sort results by this metric, ascending. Must be one of the metrics in --names.",
        )
        metrics_parser.add_argument(
            "--price-ranges",
            default=None,
            help="If given on the premises of price is also given, it should be in the format "
            "like COMPANY_ID1:12:22,COMPANY_ID2:100:",
        )
        metrics_parser.add_argument(
            "--output-csv-name",
            default=None,
            help="If given, also write the metrics result to this CSV file path.",
        )
    def _build_benchmark_parser() -> None:
        benchmark_parser = subparsers.add_parser(
            Command.BENCHMARK, help="Benchmark stocks against an index or another stock."
        )
        benchmark_parser.add_argument(
            "benchmark_pair",
            help="The benchmark and company ticker symbols, delimited by a colon, "
            "e.g. VOO:T.",
        )
        benchmark_parser.add_argument(
            "--start-date",
            required=True,
            help="Start date of the period, in ISO format, e.g. 2024-01-01.",
        )
        benchmark_parser.add_argument(
            "--end-date",
            required=True,
            help="End date of the period, in ISO format, e.g. 2026-01-01.",
        )
        benchmark_parser.add_argument(
            "--graph-directory",
            default=None,
            help="If given, save the chart as a PNG into this directory. "
            "If omitted, the chart is not saved.",
        )
    _build_metrics_parser()
    _build_benchmark_parser()
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
        stream=sys.stdout,
    )
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == Command.METRICS:
        metrics, erratic_company_ids, metrics_records_out_of_range = _run_metrics(
            names=args.metric_names,
            company_symbols=args.company_symbols,
            company_csv=args.company_csv,
            sort_by=args.sort_by,
            price_ranges_str=args.price_ranges,
        )
        print(metrics.to_string(index=False))
        if not erratic_company_ids.empty:
            print()
            print("Companies fetched with error")
            print(erratic_company_ids.to_string(index=False))
        if metrics_records_out_of_range is not None:
            print()
            print("Stocks with price out of range")
            print(metrics_records_out_of_range.to_string(index=False))

        if args.output_csv_name:
            metrics.to_csv(args.output_csv_name, index=False)
            if not erratic_company_ids.empty:
                erratic_company_ids.to_csv("companies_with_error.csv", index=False)
            if not metrics_records_out_of_range.empty:
                metrics_records_out_of_range.to_csv("alert_on_companies.csv", index=False)
    elif args.command == Command.BENCHMARK:
        try:
            benchmark_id, company_id = args.benchmark_pair.split(":")
        except ValueError:
            parser.error(
                f"argument benchmark_pair: invalid format: {args.benchmark_pair!r} "
                "(expected BENCHMARK_ID:COMPANY_ID, e.g. VOO:T)"
            )
        chart_data = _run_benchmark(
            benchmark_id=benchmark_id,
            company_id=company_id,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        benchmark_index = chart_data.benchmark_index()
        stock_index = chart_data.stock_index()
        print(
            f"Coefficient ({stock_index.symbol} vs {benchmark_index.symbol}): "
            f"{chart_data.coefficient():.4f}"
        )
        output_path = None
        if args.graph_directory:
            output_path = os.path.join(
                args.graph_directory, f"{stock_index.symbol}_vs_{benchmark_index.symbol}.png"
            )
        chart_path = _generate_benchmark_chart(chart_data, output_path=output_path)
        if chart_path is not None:
            print(f"Chart saved to {chart_path}")

    else:  # pragma: no cover - guarded by argparse's `required=True`
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
