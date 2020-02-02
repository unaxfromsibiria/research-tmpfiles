import typing
import uuid
from collections import namedtuple
from collections.abc import Iterable
from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal

from django.conf import settings
from django.utils.timezone import now as datetime_now

import requests
from rest_framework import status

from .models import CurrencyEnum
from .models import Wallet
from .models import WalletOperation

ReportRow = namedtuple("ReportRow", "dt w_from w_to amount balance")


# in transaction.atomic
def transfer_money(
    from_wallet: str, to_wallet: str, amount: Decimal, actual_retes: dict,
) -> uuid.UUID:
    """Api method to create transfer between wallets.
    amount - value in currency of wallet "from"
    actual_retes - all exchange rates for system currency (USD)
    Atomic operation in database transaction.
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(amount)

    operation = uuid.uuid4()
    from_wallet_record = Wallet.objects.get(wallet_id=from_wallet)
    to_wallet_record = Wallet.objects.get(wallet_id=to_wallet)

    assert amount <= from_wallet_record.balance, "Not enough money."
    from_wallet_record.balance -= amount
    from_rate = to_rate = 1
    base_amount = amount

    if from_wallet_record.currency != CurrencyEnum.BASE.value:
        from_rate = actual_retes.get(from_wallet_record.currency)
        assert from_rate, (
            f"No exchange rate for {from_wallet_record.currency}."
        )
        base_amount = amount * from_rate

    if to_wallet_record.currency != CurrencyEnum.BASE.value:
        to_rate = actual_retes.get(to_wallet_record.currency)
        assert to_rate, (
            f"No exchange rate for {to_wallet_record.currency}."
        )

    in_amount = base_amount * to_rate
    to_wallet_record.balance += in_amount
    info_1 = f"transfer {from_wallet} -> {to_wallet} amount -{amount}"
    info_2 = f"transfer from {from_wallet} +{in_amount} to {to_wallet}"

    WalletOperation.objects.create(
        operation=operation,
        receipt=False,
        wallet=from_wallet_record,
        info=info_1,
        currency=from_wallet_record.currency,
        rate=from_rate,
        amount=amount,
        balance=from_wallet_record.balance
    )
    WalletOperation.objects.create(
        operation=operation,
        receipt=True,
        wallet=to_wallet_record,
        info=info_2,
        currency=to_wallet_record.currency,
        rate=to_rate,
        amount=in_amount,
        balance=to_wallet_record.balance
    )
    from_wallet_record.save()
    to_wallet_record.save()

    return operation


def get_actual_exchange_rates(logger) -> dict:
    """Request rates data from internal system service.
    """
    result = {}
    if not settings.RATE_SERVICE_URLS:
        logger.critical("Wrong service configuration 'RATE_SERVICE_URLS'.")

    for url in settings.RATE_SERVICE_URLS:
        try:
            resp = requests.get(url)
        except Exception as err:
            logger.error(f"Problem with service '{url}': {err}")
            continue

        if resp.status_code != status.HTTP_200_OK:
            logger.error(f"In service '{url}' status: {resp.status_code}")
            logger.debug(f"From '{url}' gotten: {resp.text}")
            continue

        currency_list = []
        try:
            data = resp.json()
            if sum(data.values()):
                currency_list.extend(data.keys())

        except Exception as err:
            logger.error(f"Data format error in service '{url}': {err}")
            logger.debug(f"Source: {resp.text}")
            continue
        else:
            result.update(data)
            logger.info(f"From '{url}' rates for {','.join(currency_list)}")
            break

    if not result:
        logger.critical("No actual exchange rates!")

    return result


# in transaction.atomic
def topup_money(wallet: str, amount: Decimal) -> uuid.UUID:
    """Api method to top up wallet balance.
    """

    operation = uuid.uuid4()
    wallet_record = Wallet.objects.get(wallet_id=wallet)
    assert amount > 0, "Incorrect amount."

    wallet_record.balance += amount
    info = f"top up {wallet_record} in +{amount}"

    WalletOperation.objects.create(
        operation=operation,
        receipt=True,
        wallet=wallet_record,
        info=info,
        currency=wallet_record.currency,
        rate=1,
        amount=amount,
        balance=wallet_record.balance
    )
    wallet_record.save()

    return operation


def report_data(
    wallet: str, start_date: date, end_date: date, **kwargs
) -> typing.Generator[ReportRow, None, None]:
    """Operations info for report.
    """
    now = datetime_now()
    # period
    start = datetime.combine(start_date, time.min).replace(tzinfo=now.tzinfo)
    end = datetime.combine(end_date, time.max).replace(tzinfo=now.tzinfo)

    records = WalletOperation.objects.filter(
        wallet__wallet_id=wallet, created__range=(start, end)
    ).values_list(
        "created", "receipt", "info", "amount", "balance"
    ).order_by("created")

    for dt, receipt, info, amount, balance in records.iterator():
        if receipt:
            amount = f"+ {amount}"
            to_info = wallet
            if "transfer from" in info:
                _, _, from_info, *_ = info.split(" ", 3)
            else:
                from_info = "-"
        else:
            amount = f"- {amount}"
            from_info = wallet
            _, _, _, to_info, *_ = info.split(" ", 4)

        yield ReportRow(dt.isoformat(), from_info, to_info, amount, balance)
