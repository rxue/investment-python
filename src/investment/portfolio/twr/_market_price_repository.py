from datetime import date, datetime
from typing import Final

from investment.marketquote.repository import (
    fetch_fx_rate_series_from_euro,
    fetch_historical_prices,
)
from investment.util.util import EUR, convert_to_euro_cent
from investment.vo.value_objects import FxRateSeries, Period, Price, PriceSeries

_fx_rate_series_cache:dict[str,FxRateSeries] = dict()
def _find_historical_euro_price_series(security_id:str, period:Period) -> PriceSeries:
    price_series = fetch_historical_prices(security_id, period)
    def fetch_price_in_euro(existing_price: Price) -> Price:
        currency: Final = existing_price.currency
        if currency == EUR:
            return existing_price
        else:
            if currency not in _fx_rate_series_cache:
                _fx_rate_series_cache[currency] = fetch_fx_rate_series_from_euro(currency, period)
            fx_rate = _fx_rate_series_cache[currency].get(existing_price.date())
            price_value_in_euro = convert_to_euro_cent(existing_price, fx_rate)
            return Price(price_value_in_euro, EUR, existing_price.timestamp)
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

class MarketPriceRepository:
    def __init__(self, end_date: date) -> None:
        self.end_date = end_date
        self.series_cache: dict[str, PriceSeries] = {}
    def find_euro_price(self, security_id:str, date:date) -> Price:
        price_series = self.series_cache.get(security_id)
        if price_series is None:
            period = Period(from_date=date, to_date=self.end_date)
            price_series = _find_historical_euro_price_series(security_id, period)
            self.series_cache[security_id] = price_series
        return price_series.get_price(date)
