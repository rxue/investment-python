from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum, auto
from typing import NamedTuple, Protocol


def _money_to_cent_value(money: Decimal) -> int:
    return int((money * 100).to_integral_value(rounding=ROUND_HALF_UP))


class Transaction(Protocol):
    date:date
    money:Decimal
    def cent_value(self) -> int: ...
    def is_external_cashflow(self) -> bool: ...


class Action(Enum):
    BUY = auto()
    SELL = auto()


class Trade(NamedTuple):
    security_id: str
    action:Action
    share_amount:int
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return False

class Dividend(NamedTuple):
    security_id: str
    share_amount:int
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return False

class Deposit(NamedTuple):
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return True

class Expense(NamedTuple):
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return True
