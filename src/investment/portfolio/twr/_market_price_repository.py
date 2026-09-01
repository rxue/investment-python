from datetime import datetime

from investment.marketquote.repository import fetch_historical_prices, fetch_price_in_euro
from investment.util.constants import EUR
from investment.vo.value_objects import Period, Price, PriceSeries


def find_historical_euro_price_series(security_id:str, period:Period) -> PriceSeries:
    price_series = fetch_historical_prices(security_id, period)

    euro_cent_prices = {
        trading_date: fetch_price_in_euro(
            Price(
                cent_value,
                price_series.currency,
                datetime.combine(trading_date, datetime.min.time()),
            )
        ).cent_value
        for trading_date, cent_value in price_series.cent_prices.items()
    }
    return PriceSeries(currency=EUR, cent_prices=euro_cent_prices)
