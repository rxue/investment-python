from datetime import datetime
from typing import NamedTuple


class Price(NamedTuple):
    cent_value:int
    currency: str
    timestamp: datetime
