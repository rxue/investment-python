from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import NamedTuple


class Price(NamedTuple):
    cent_value:int
    currency: str
    timestamp: datetime
    def amount(self) -> float:
        return self.cent_value / 100
    def value_with_currency(self) -> str:
        return f"{self.amount()} {self.currency}"
    def date(self) -> date:
        return self.timestamp.date()

class FxRateSeries(NamedTuple):
    base_currency: str
    quote_currency: str
    values:dict[date,Decimal]
    def get(self, date:date) -> Decimal:
        """Return the rate on ``date``, falling back to the most recent
        earlier date in the series (e.g. a weekend or holiday has no rate
        of its own, so this walks backwards to the last published date)."""
        search_date = date
        while search_date not in self.values:
            search_date -= timedelta(days=1)
            if search_date < min(self.values):
                raise KeyError(f"no rate on or before {date} in the series")
        return self.values[search_date]

class Percentage(NamedTuple):
    fraction_value:float
    def percent_value(self) -> float:
        return round(self.fraction_value * 100, 2)

class Period(NamedTuple):
    from_date:date
    to_date:date

class PriceSeries(NamedTuple):
    currency:str
    cent_prices:dict[date,int]
    def get_price(self, date:date) -> Price:
        """Return the price on ``date``, falling back to the most recent
        earlier date in the series (e.g. a weekend or holiday has no price
        of its own, so this walks backwards to the last trading day)."""
        search_date = date
        while search_date not in self.cent_prices:
            search_date -= timedelta(days=1)
            if search_date < min(self.cent_prices):
                raise KeyError(f"no price on or before {date} in the series")
        return Price(
            cent_value=self.cent_prices[search_date],
            currency=self.currency,
            timestamp=datetime.combine(search_date, datetime.min.time()),
        )
