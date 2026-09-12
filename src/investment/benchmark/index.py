from investment.marketquote.repository import fetch_historical_prices
from investment.util.util import EUR
from investment.vo.value_objects import IndexSeries, Period


def _get_index_series(security_id:str, period:Period, currency:str|None) -> tuple[str,IndexSeries]:
    """Fetch ``security_id``'s historical price series over ``period``, in
    ``currency``, and rebase it to 100 at its first date."""
    price_series = fetch_historical_prices(security_id, period, currency=currency)
    first_price = next(iter(price_series.cent_prices.values()))
    value_by_date = {
        trading_date: cent_price / first_price * 100
        for trading_date, cent_price in price_series.cent_prices.items()
    }
    result_currency = price_series.currency if currency is None else currency
    return result_currency, IndexSeries(label=security_id, value_by_date=value_by_date)

def get_stock_index_series(security_id:str, period:Period, currency:str=EUR) -> IndexSeries:
    """Fetch ``security_id``'s historical price series over ``period``, in
    ``currency``, and rebase it to 100 at its first date."""
    _,index_series = _get_index_series(security_id, period, currency)
    return index_series

def get_benchmark_index_series(benchmark_id:str, period:Period) -> tuple[str,IndexSeries]:
    """Fetch ``security_id``'s historical price series over ``period``, in
    ``currency``, and rebase it to 100 at its first date."""
    return  _get_index_series(benchmark_id, period, None)
