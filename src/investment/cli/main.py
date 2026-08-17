"""Command-line entry point for the investment toolkit.

Usage examples::

    investment-python price AAPL
    investment-python price AAPL --date 2026-08-01
    investment-python fundamentals AAPL --metrics trailingPE dividendYield
"""
import argparse
from datetime import date
from typing import Sequence

from investment.marketquote import fetcher


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment", description="Fetch market quotes and fundamentals."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser("price", help="Fetch the price for a symbol.")
    price_parser.add_argument("symbol", help="Company ticker symbol, e.g. AAPL")
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


def _run_price(symbol: str, target_date: date | None) -> dict:
    return fetcher.fetch_price(symbol, target_date)._asdict()


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "price":
        result = _run_price(args.symbol, args.date)
    elif args.command == "fundamentals":
        result = fetcher.fetch_fundamental_metrics(args.symbol, args.metrics)
    else:  # pragma: no cover - guarded by argparse's `required=True`
        parser.error(f"Unknown command: {args.command}")
        return

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
