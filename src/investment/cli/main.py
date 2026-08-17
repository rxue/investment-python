"""Command-line entry point for the investment toolkit.

Usage examples::

    investment-python price AAPL
    investment-python price AAPL --date 2026-08-01
    investment-python fundamentals AAPL --metrics trailingPE dividendYield
"""
import argparse
from datetime import date
from typing import Sequence

import pandas as pd

from investment.marketquote import fetcher

from investment.cli.watch_list import PriceRow


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment", description="Fetch market quotes and fundamentals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser("price", help="Fetch the price for a symbol.")
    price_parser.add_argument("symbols", help="Company ticker symbols delimited by comma, e.g. AAPL,ELISA.HE")
    price_parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="Fetch the close price on or before this date (YYYY-MM-DD). "
        "Defaults to the current quoted price.",
    )

    fundamentals_parser = subparsers.add_parser(
        "fundamentals", help="Fetch fundamental metrics for a symbol."
    )
    fundamentals_parser.add_argument("symbol", help="Company ticker symbol, e.g. AAPL")
    fundamentals_parser.add_argument(
        "--metrics",
        nargs="+",
        required=True,
        choices=[metric.value for metric in fetcher.FundamentalMetric],
        help="One or more fundamental metrics to fetch.",
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


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "price":
        prices = _run_price(args.symbols, args.date)
        print(prices.to_string(index=False))
    elif args.command == "fundamentals":
        metrics = fetcher.fetch_fundamental_metrics(args.symbol, args.metrics)
        for key, value in metrics.items():
            print(f"{key}: {value}")
    else:  # pragma: no cover - guarded by argparse's `required=True`
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
