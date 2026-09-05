"""Integration tests for ``calculation.calculate_twr``.

These hit the real Yahoo Finance and ECB APIs over the network (no
mocking) - hence "IT" rather than a unit test.
"""
import calendar
from datetime import date
from decimal import Decimal

import pytest

from investment.portfolio.transaction import Action, Trade
from investment.portfolio.twr.calculation import calculate_twr

pytestmark = pytest.mark.integration


def test_calculate_twr_with_two_buy_transactions():
    """Two BUYs of PFE shares - 10 shares for 250 EUR on the first trade
    date, then 20 more shares for 500 EUR on the second trade date -
    produce one daily snapshot per calendar day from the first trade date
    through the last day of the last trade date's month (not just through
    the last trade date itself), with the position and cash reflecting both
    trades by the last day and a daily return for every day after the first.
    """
    first_trade_date = date(2025, 12, 24)
    second_trade_date = date(2025, 12, 29)
    last_day_of_month = calendar.monthrange(second_trade_date.year, second_trade_date.month)[1]
    end_date = second_trade_date.replace(day=last_day_of_month)
    buy_10_pfe_shares = Trade(
        security_id="PFE",
        action=Action.BUY,
        share_amount=10,
        date=first_trade_date,
        money=Decimal("-250"),
    )
    buy_20_pfe_shares = Trade(
        security_id="PFE",
        action=Action.BUY,
        share_amount=20,
        date=second_trade_date,
        money=Decimal("-500"),
    )

    snapshots, daily_returns = calculate_twr([buy_10_pfe_shares, buy_20_pfe_shares])

    expected_snapshot_count = (end_date - first_trade_date).days + 1
    assert len(snapshots) == expected_snapshot_count
    assert len(daily_returns) == expected_snapshot_count - 1

    first_snapshot = snapshots[0]
    assert first_snapshot.date == first_trade_date
    assert first_snapshot.cash_in_cent == -25000
    first_holding = first_snapshot.holdings.holding_by_security["PFE"]
    assert first_holding.position == 10

    last_snapshot = snapshots[-1]
    assert last_snapshot.date == end_date
    assert last_snapshot.cash_in_cent == -75000

    last_holding = last_snapshot.holdings.holding_by_security["PFE"]
    assert last_holding.position == 30
    assert last_holding.price_in_cent is not None
    assert last_holding.price_in_cent > 0

    assert last_snapshot.value_in_cent() == (
        last_snapshot.cash_in_cent + last_holding.market_value_in_cent()
    )
