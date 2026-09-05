from decimal import Decimal
from typing import Final

from investment.vo.value_objects import Price

EUR:Final[str] = "EUR"

def convert_to_euro_cent(existing_price: Price, fx_rate: Decimal) -> int:
    if existing_price.currency == "GBp":
        return round((existing_price.cent_value / Decimal(100)) / fx_rate)
    return round(existing_price.cent_value / fx_rate)
