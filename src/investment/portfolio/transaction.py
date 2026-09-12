import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum, auto
from typing import NamedTuple, Protocol

from investment.vo.value_objects import Period


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

class ExpenseType(Enum):
    INVESTMENT = auto()
    NON_INVESTMENT = auto()

class Expense(Transaction, Protocol):
    def type(self) -> ExpenseType:...

class InvestmentExpense(NamedTuple):
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return False
    def type(self):
        return ExpenseType.INVESTMENT

class NonInvestmentExpense(NamedTuple):
    date: date
    money:Decimal
    def cent_value(self) -> int:
        return _money_to_cent_value(self.money)
    def is_external_cashflow(self) -> bool:
        return True
    def type(self):
        return ExpenseType.NON_INVESTMENT

def get_period(transactions:list[Transaction]) -> Period:
    start_date = transactions[0].date
    last_date = transactions[-1].date
    last_day_of_month = calendar.monthrange(last_date.year, last_date.month)[1]
    return Period(start_date,last_date.replace(day=last_day_of_month))
