from datetime import datetime
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
        return self.fraction_value * 100

