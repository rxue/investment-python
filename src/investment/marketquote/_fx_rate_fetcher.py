import csv
import io
import logging
from datetime import date, timedelta
from decimal import Decimal
from functools import cache

import requests

from investment.util.constants import EUR

logger = logging.getLogger(__name__)

@cache
def fetch_fx_rate_to_euro(base_currency: str, target_date: date) -> tuple[date, float]:
    """Fetch the ``base_currency``-to-EUR exchange rate for ``date`` from the ECB
    (European Central Bank).

    Returns ``1.0`` for ``date`` unchanged when ``base_currency`` is already ``'EUR'``.
    For a past ``date``, requests that day's rate from the ECB data API. For today
    or a future ``date``, requests the latest available observation instead, since
    the ECB has no rate published yet for those.

    Because the ECB only publishes rates for business days, the returned date may
    differ from the requested ``date`` (e.g. a weekend or holiday falls back to the
    most recent prior business day).

    :param base_currency: ISO 4217 currency code to convert from (e.g. ``'USD'``).
    :param target_date: the date to fetch the rate for.
    :return: a tuple of the actual observation date and the exchange rate.
    :raises requests.HTTPError: if the ECB API request fails.
    :raises StopIteration: if the API response contains no observations.
    """
    if base_currency == EUR:
        return target_date, 1
    url = f"https://data-api.ecb.europa.eu/service/data/EXR/D.{base_currency}.EUR.SP00.A"
    today = date.today()
    if target_date < today:
        date_str = target_date.strftime("%Y-%m-%d")
        response = requests.get(url, params={
            "startPeriod": date_str,
            "endPeriod": date_str,
            "format": "csvdata",
        })
    else:
        logger.info(f"Fetch FX rate for {target_date}")
        response = requests.get(url, params={
            "lastNObservations": 1,
            "format": "csvdata",
        })
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.text))
    row = next(reader)
    return target_date.fromisoformat(row["TIME_PERIOD"]), float(row["OBS_VALUE"])

@cache
def fetch_fx_rate_to_euro_series(
    base_currency: str, start_date: date, end_date: date
) -> list[tuple[date, Decimal]]:
    """Fetch the ``base_currency``-to-EUR exchange rate for every day the ECB
    published one between ``start_date`` and ``end_date`` (both inclusive),
    in a single request.

    Returns ``(day, Decimal("1"))`` for every calendar day in the range
    unchanged when ``base_currency`` is already ``'EUR'``.

    Because the ECB only publishes rates for business days, the result has
    no entry for weekends/holidays within the range - callers wanting a
    rate for one of those days should fall back to the most recent earlier
    date present in the result (as ``PriceSeries.get_price`` does for
    security prices).

    :param base_currency: ISO 4217 currency code to convert from (e.g. ``'USD'``).
    :param start_date: first date of the range to fetch, inclusive.
    :param end_date: last date of the range to fetch, inclusive.
    :return: a list of ``(date, rate)`` tuples, ascending by date.
    :raises requests.HTTPError: if the ECB API request fails.
    """
    if base_currency == EUR:
        return [
            (start_date + timedelta(days=offset), Decimal("1"))
            for offset in range((end_date - start_date).days + 1)
        ]
    url = f"https://data-api.ecb.europa.eu/service/data/EXR/D.{base_currency}.EUR.SP00.A"
    logger.info(f"Fetch FX rate series for {base_currency} from {start_date} to {end_date}")
    response = requests.get(url, params={
        "startPeriod": start_date.strftime("%Y-%m-%d"),
        "endPeriod": end_date.strftime("%Y-%m-%d"),
        "format": "csvdata",
    })
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.text))
    return [
        (date.fromisoformat(row["TIME_PERIOD"]), Decimal(row["OBS_VALUE"]))
        for row in reader
    ]
