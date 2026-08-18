from typing import NamedTuple, Any

from investment.vo.value_objects import Price


def _readable_time(timestamp) -> str:
    """Format ``timestamp`` with its timezone name (e.g. "Helsinki") instead
    of a numeric UTC offset."""
    formatted = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    tz = timestamp.tzinfo
    tz_key = getattr(tz, "key", None)
    if tz_key:
        tz_name = tz_key.replace("_", " ")
        formatted = f"{formatted} {tz_name}"
    return formatted


class PriceRow(NamedTuple):
    company:str
    price:Price

    def to_readable_dict(self) -> dict[str,Any]:
        return {
            "company": self.company,
            "price": self.price.cent_value / 100,
            "currency": self.price.currency,
            "time": _readable_time(self.price.timestamp),
        }

