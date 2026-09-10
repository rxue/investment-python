from datetime import date

from investment.marketquote.repository import fetch_historical_prices
from investment.util.util import EUR
from investment.vo.value_objects import FxRateSeries, Period, Price, PriceSeries

_fx_rate_series_cache:dict[str,FxRateSeries] = dict()

class MarketPriceRepository:
    def __init__(self, end_date: date) -> None:
        self.end_date = end_date
        self.series_cache: dict[str, PriceSeries] = {}
    def find_price(self, security_id:str, date:date, currency:str=EUR) -> Price:
        price_series = self.series_cache.get(security_id)
        if price_series is None:
            period = Period(from_date=date, to_date=self.end_date)
            price_series = fetch_historical_prices(security_id, period, currency)
            self.series_cache[security_id] = price_series
        return price_series.get_price(date)
