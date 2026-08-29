# investment-python

A command-line tool for pulling stock market quotes and fundamentals (price,
P/E, ROE, P/B, dividend yield, and more) for a watch list of companies given
as ticker symbols or a CSV file. It can sort the results, flag stocks trading
outside a given price range, and export everything to CSV.

## Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) for dependency management and running the tool

Install dependencies with:

```
uv sync
```

Then run the tool with `uv run investment ...`.

example command: `uv run investment metrics COMPANY_NAME,PRICE,REGULAR_MARKET_CHANGE_PERCENT,PRICE_IN_EURO,TRAILING_PE,RETURN_ON_EQUITY,PRICE_TO_BOOK,DIVIDEND_YIELD --sort-by REGULAR_MARKET_CHANGE_PERCENT --company-symbols ELISA.HE,FIA1S.HE,NOVO-B.CO`
