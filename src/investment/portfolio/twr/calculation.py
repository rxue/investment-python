import calendar
from datetime import date, timedelta
from typing import Final, NamedTuple

from investment.portfolio.transaction import Action, Deposit, Trade, Transaction
from investment.portfolio.twr._market_price_repository import MarketPriceRepository
from investment.portfolio.twr.portfolio import Holding, Holdings, PortfolioSnapshot
from investment.vo.value_objects import Period


class DailyReturn(NamedTuple):
    date: date
    value: float

class DailyReturnSeries(NamedTuple):
    series: list[DailyReturn]

class _PortfolioSnapshotSeriesGenerator:
    def __init__(self, transactions:list[Transaction]) -> None:
        self.transactions = transactions
        self.market_price_repository = MarketPriceRepository(self._get_end_date())
    def generate(self) -> dict[date,PortfolioSnapshot]:
        # Assumes transactions is already sorted by date ascendingly: the last
        # element is taken as the end date, and snapshots are chained in the
        # order dates are first seen below.
        def group_transactions_by_date() -> dict[date, list[Transaction]]:
            transactions_by_date: dict[date, list[Transaction]] = {}
            for transaction in self.transactions:
                transactions_by_date.setdefault(transaction.date, []).append(transaction)
            return transactions_by_date

        transactions_by_date = group_transactions_by_date()

        first_date = self.transactions[0].date
        previous_portfolio_snapshot = PortfolioSnapshot(first_date, 0, Holdings({}), [])
        portfolio_snapshots:dict[date,PortfolioSnapshot] = {}
        for _date, daily_transactions in transactions_by_date.items():
            snapshot = self._new_snapshot(daily_transactions, previous_portfolio_snapshot)
            previous_portfolio_snapshot = portfolio_snapshots[_date] = snapshot
        return self._add_missing_snapshots(portfolio_snapshots)

    def _get_end_date(self) -> date:
        last_date = self.transactions[-1].date
        last_day_of_month = calendar.monthrange(last_date.year, last_date.month)[1]
        return last_date.replace(day=last_day_of_month)

    def _new_snapshot(
        self, daily_transactions:list[Transaction], previous_snapshot:PortfolioSnapshot
    ) -> PortfolioSnapshot:
        # date
        _date:Final[date] = daily_transactions[-1].date
        # calculate remaining cash in cent
        remaining_cash_in_cent:int = previous_snapshot.cash_in_cent
        for transaction in daily_transactions:
            remaining_cash_in_cent += transaction.cent_value()
        # calculate holdings
        holdings = Holdings(previous_snapshot.holdings.holding_by_security.copy())
        for transaction in daily_transactions:
            if isinstance(transaction, Trade):
                trade = transaction
                if trade.action == Action.BUY:
                    holdings.add(trade.security_id, trade.share_amount)
                elif trade.action == Action.SELL:
                    holdings.remove(trade.security_id, trade.share_amount)
        ## add price to holdings
        holdings_with_price = self._reprice_holdings(holdings.holding_by_security, _date)
        # calculate external cash flow
        external_cash_flows = [
            transaction.cent_value()
            for transaction in daily_transactions
            if isinstance(transaction, Deposit)
        ]
        return PortfolioSnapshot(
            _date, remaining_cash_in_cent, Holdings(holdings_with_price), external_cash_flows
        )

    def _add_missing_snapshots(
        self, existing_snapshots:dict[date,PortfolioSnapshot]
    ) -> dict[date,PortfolioSnapshot]:
        # Daily TWR needs a valuation for every day in the period, not just
        # transaction days - a day with no transactions still has to reflect
        # that day's market move. existing_snapshots[period.from_date] is
        # guaranteed present since transactions[0].date is a transaction date.
        period:Period = Period(self.transactions[0].date, self._get_end_date())

        def carry_forward_snapshot(
            previous_snapshot:PortfolioSnapshot, _date:date
        ) -> PortfolioSnapshot:
            """A day with no transactions still needs a snapshot: carry the
            previous day's cash and holdings forward, re-pricing the holdings
            for ``_date`` (positions are unchanged, but market value isn't)."""
            holding_by_security = previous_snapshot.holdings.holding_by_security
            holdings_with_price = self._reprice_holdings(holding_by_security, _date)
            return PortfolioSnapshot(
                _date, previous_snapshot.cash_in_cent, Holdings(holdings_with_price), []
            )

        complete_snapshots: dict[date,PortfolioSnapshot] = {}
        previous_snapshot = existing_snapshots[period.from_date]
        current_date = period.from_date
        while current_date <= period.to_date:
            if current_date in existing_snapshots:
                previous_snapshot = existing_snapshots[current_date]
            else:
                previous_snapshot = carry_forward_snapshot(previous_snapshot, current_date)
            complete_snapshots[current_date] = previous_snapshot
            current_date += timedelta(days=1)
        return complete_snapshots

    def _reprice_holdings(
        self, holding_by_security:dict[str,Holding], _date:date
    ) -> dict[str,Holding]:
        return {
            security_id: Holding(
                holding.position,
                self.market_price_repository.find_euro_price(security_id, _date).cent_value,
            )
            for security_id, holding in holding_by_security.items()
        }

def calculate_twr(
    transactions: list[Transaction],
) -> tuple[list[PortfolioSnapshot], list[DailyReturn]]:
    """Compute a daily-linked time-weighted return series from a portfolio's
    transaction history.

    ``transactions`` MUST already be sorted by date, ascending. This is a
    precondition the caller is responsible for, not something this function
    (or ``_PortfolioSnapshotsGenerator``) checks or sorts for you - passing
    unsorted transactions produces silently wrong snapshots and returns
    rather than raising, since end date, first date, and the day-by-day
    snapshot chain are all derived from list/insertion order rather than by
    re-sorting internally.

    Returns a ``(portfolio_snapshots, daily_return_series)`` tuple:
    - ``portfolio_snapshots``: one ``PortfolioSnapshot`` per distinct
      transaction date, in the same (assumed ascending) order.
    - ``daily_return_series``: for each date after the first, the return
      ``(value_today - external_cashflow_today) / value_yesterday - 1``,
      so that deposits/withdrawals don't get counted as investment
      performance. No return is produced for the first date, since there is
      no prior snapshot to compare against.
    """
    # Step 1: form the map from date to portfolio snapshot for each day
    snapshots = _PortfolioSnapshotSeriesGenerator(transactions).generate()
    dates = list(snapshots)

    # Step 2: chain daily returns, each day's cashflow-adjusted change over the previous day
    daily_returns: list[DailyReturn] = []
    for previous_date, current_date in zip(dates, dates[1:]):
        previous_value = snapshots[previous_date].value_in_cent()
        current_snapshot = snapshots[current_date]
        current_value = current_snapshot.value_in_cent()
        cash_flow = current_snapshot.external_cash_flow_value_in_cent()
        daily_return = (
            0.0 if previous_value == 0
            else (current_value - cash_flow) / previous_value - 1
        )
        daily_returns.append(DailyReturn(current_date, daily_return))

    return [snapshots[d] for d in dates], daily_returns

