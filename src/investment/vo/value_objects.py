from datetime import date, datetime
from typing import NamedTuple


class Price(NamedTuple):
    cent_value:int
    currency: str
    timestamp: datetime
    def amount(self) -> float:
        return self.cent_value / 100
    def value_with_currency(self) -> str:
        return f"{self.amount()} {self.currency}"
    def currency_value(self) -> str:
        return self.currency.upper()

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
