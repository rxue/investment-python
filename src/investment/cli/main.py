"""Command-line entry point for the investment toolkit.

Usage examples::

    investment-python price AAPL
    investment-python price AAPL --date 2026-08-01
    investment-python metrics PRICE,TRAILING_PE --company-symbols AAPL
"""
import argparse
import logging
import sys
import time
from datetime import date
from enum import StrEnum
from typing import Sequence

import pandas as pd

from investment.cli.row import PriceRow
from investment.marketquote import repository
from investment.util.decorator import clock

logger = logging.getLogger(__name__)

class Command(StrEnum):
    PRICE = "price"
    METRICS = "metrics"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment", description="Fetch market quotes and fundamentals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser(Command.PRICE, help="Fetch the price for a symbol.")
    price_parser.add_argument(
        "symbols", help="Company ticker symbols delimited by comma, e.g. AAPL,ELISA.HE"
    )
    price_parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="Fetch the close price on or before this date (YYYY-MM-DD). "
        "Defaults to the current quoted price.",
    )

    def _build_metrics_parser() -> None:
        metrics_parser = subparsers.add_parser(
            Command.METRICS, help="Fetch metrics for symbols."
        )
        metrics_parser.add_argument(
            "names",
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
            "--output-csv-name",
            default=None,
            help="If given, also write the metrics result to this CSV file path.",
        )
        metrics_parser.add_argument(
            "--sort-by",
            default=None,
            help="Sort results by this metric, ascending. Must be one of the metrics in --names.",
        )

    _build_metrics_parser()

    return parser


def _run_price(symbols: str, target_date: date | None) -> pd.DataFrame:
    """Fetch the price for one or more comma-delimited symbols.

    Returns a pandas DataFrame with one row per symbol.
    """
    rows = []
    for symbol in symbols.split(","):
        symbol = symbol.strip()
        price = repository.fetch_price(symbol, target_date)
        price_row=PriceRow(symbol, price)
        rows.append(price_row.to_readable_dict())
    return pd.DataFrame(rows)

def _load_company_symbols(csv_source: str) -> str:
    """Load comma-delimited Yahoo ticker symbols from a company CSV file.

    ``csv_source`` may be a local file path or an http(s) URL. The CSV must
    contain a "Yahoo Company Symbol" column, e.g.
    https://gist.githubusercontent.com/rxue/7ec0914a8af1525d97e8dfd2ac5d61d7/raw/companies.csv
    """
    companies = pd.read_csv(csv_source)
    return ",".join(companies["Yahoo Company Symbol"].astype(str))



@clock
def _run_metrics(symbols: str, names: str, sort_by: str | None = None) -> pd.DataFrame:
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

    company_id_list = [symbol.strip() for symbol in symbols.split(",")]
    batch_size = 100
    if len(company_id_list) > batch_size:
        rows = []
        for i in range(0, len(company_id_list), batch_size):
            batch = company_id_list[i:i + batch_size]
            rows.extend(repository.fetch_current_metrics_batch(batch, metric_list, True))
            logger.info("Executed one batch")
            time.sleep(60)
    else:
        rows = repository.fetch_current_metrics_batch(company_id_list, metric_list, True)

    if sort_by_metric is not None:
        rows = repository.sort_records(rows, sort_by_metric)

    return pd.DataFrame([r.to_readable() for r in rows])

def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == Command.PRICE:
        prices = _run_price(args.symbols, args.date)
        print(prices.to_string(index=False))
    elif args.command == Command.METRICS:
        company_symbols = args.company_symbols or _load_company_symbols(args.company_csv)
        metrics = _run_metrics(company_symbols, args.names, args.sort_by)
        print(metrics.to_string(index=False))
        if args.output_csv_name:
            metrics.to_csv(args.output_csv_name, index=False)
    else:  # pragma: no cover - guarded by argparse's `required=True`
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
