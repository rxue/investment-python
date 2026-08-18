"""Command-line entry point for the investment toolkit.

Usage examples::

    investment-python price AAPL
    investment-python price AAPL --date 2026-08-01
    investment-python metrics PRICE,TRAILING_PE --company-symbols AAPL
"""
import argparse
from datetime import date
from enum import StrEnum
from typing import Sequence

import pandas as pd

from investment.marketquote import fetcher

from investment.cli.row import PriceRow

class Command(StrEnum):
    PRICE = "price"
    METRICS = "metrics"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment", description="Fetch market quotes and fundamentals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser(Command.PRICE, help="Fetch the price for a symbol.")
    price_parser.add_argument("symbols", help="Company ticker symbols delimited by comma, e.g. AAPL,ELISA.HE")
    price_parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="Fetch the close price on or before this date (YYYY-MM-DD). "
        "Defaults to the current quoted price.",
    )

    metrics_parser = subparsers.add_parser(
        Command.METRICS, help="Fetch metrics for symbols."
    )
    metrics_parser.add_argument(
        "names",
        help="One or more metrics to fetch, delimited by comma, e.g. PRICE,TRAILING_PE. "
        f"Choose from {', '.join(metric.name for metric in fetcher.Metric)}.",
    )
    metrics_parser.add_argument(
        "--company-symbols",
        required=True,
        help="Company ticker symbols delimited by comma, e.g. AAPL,ELISA.HE",
    )

    return parser


def _run_price(symbols: str, target_date: date | None) -> pd.DataFrame:
    """Fetch the price for one or more comma-delimited symbols.

    Returns a pandas DataFrame with one row per symbol.
    """
    rows = []
    for symbol in symbols.split(","):
        symbol = symbol.strip()
        price = fetcher.fetch_price(symbol, target_date)
        price_row=PriceRow(symbol, price)
        rows.append(price_row.to_readable_dict())
    return pd.DataFrame(rows)

def _run_metrics(symbols: str, names: str) -> pd.DataFrame:
    metric_names = [name.strip() for name in names.split(",")]
    try:
        metric_list = [fetcher.Metric[name] for name in metric_names]
    except KeyError as exc:
        valid_names = ", ".join(metric.name for metric in fetcher.Metric)
        raise SystemExit(
            f"investment metrics: error: argument --names: invalid choice: {exc.args[0]!r} "
            f"(choose from {valid_names})"
        ) from None
    rows = []
    for symbol in symbols.split(","):
        symbol = symbol.strip()
        metrics_record = fetcher.fetch_current_metrics(symbol, metric_list)
        rows.append(metrics_record.to_readable())
    return pd.DataFrame(rows)

def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == Command.PRICE:
        prices = _run_price(args.symbols, args.date)
        print(prices.to_string(index=False))
    elif args.command == Command.METRICS:
        metrics = _run_metrics(args.company_symbols, args.names)
        print(metrics.to_string(index=False))
    else:  # pragma: no cover - guarded by argparse's `required=True`
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
