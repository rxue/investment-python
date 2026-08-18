from datetime import datetime
from typing import NamedTuple


class Price(NamedTuple):
    cent_value:int
    currency: str
    timestamp: datetime
    def value(self) -> str:
        return f"{self.cent_value / 100} {self.currency}"
