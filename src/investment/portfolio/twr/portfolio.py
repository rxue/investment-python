from dataclasses import dataclass
from datetime import date
from typing import NamedTuple


class Holding(NamedTuple):
    position:int
    price_in_cent:int | None = None
    def market_value_in_cent(self) -> int:
        return self.position * (self.price_in_cent or 0)

@dataclass
class Holdings:
    holding_by_security: dict[str,Holding]
    def add(self, security_id:str, position:int):
        existing = self.holding_by_security.get(security_id, Holding(0))
        updated_position = existing.position + position
        self.holding_by_security[security_id] = Holding(updated_position, existing.price_in_cent)
    def remove(self, security_id:str, position:int):
        existing = self.holding_by_security.get(security_id, Holding(0))
        updated_position = existing.position - position
        self.holding_by_security[security_id] = Holding(updated_position, existing.price_in_cent)

class PortfolioSnapshot(NamedTuple):
    date:date
    # Running cash balance as of `date` - carried forward and adjusted from
    # the previous snapshot, not reset per day.
    cash_balance_in_cent:int
    holdings:Holdings
    # External cash-flow transaction amounts (deposits, non-investment
    # expenses) that occurred on the `date` only - NOT cumulative; reset to []
    # for every snapshot, including carried-forward no-transaction days.
    external_cash_flows:list[int]
    def value_in_cent(self) -> int:
        holdings = self.holdings.holding_by_security.values()
        holdings_value = sum(h.market_value_in_cent() for h in holdings)
        return self.cash_balance_in_cent + holdings_value
    def total_external_cash_flow_in_cent(self) -> int:
        return sum(self.external_cash_flows)

class PortfolioSnapshotSeries(NamedTuple):
    currency:str
    snapshots:list[PortfolioSnapshot]


