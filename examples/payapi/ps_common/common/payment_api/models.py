import uuid
from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models

money_sum = dict(default=0, max_digits=8, decimal_places=2)


def random_wallet_id() -> str:
    return f"{uuid.uuid4().int}"


def enum_to_choices(enum_cls: Enum) -> list:
    return sorted(
        (str_val, e_val.value)
        for str_val, e_val in CurrencyEnum._value2member_map_.items()
    )


class CurrencyEnum(Enum):
    """System currency.
    """
    BASE = "USD"

    USD = "USD"
    EUR = "EUR"
    CAD = "CAD"
    CNY = "CNY"


class Wallet(AbstractUser):
    """System user model.
    """

    created = models.DateTimeField("Created", auto_now_add=True)
    wallet_id = models.TextField("Wallet", default=random_wallet_id)
    currency = models.TextField(
        "Currency",
        default=CurrencyEnum.BASE.value,
        choices=enum_to_choices(CurrencyEnum)
    )
    balance = models.DecimalField("Balance", **money_sum)
    city = models.TextField("City", default="")
    country = models.TextField("Country", default="")

    class Meta:
        db_table = "payment_wallet"

    def __str__(self) -> str:
        return f"{self.balance} {self.currency} in {self.wallet_id}"


class WalletOperation(models.Model):
    """Opration with wallet.
    """
    operation = models.UUIDField("Operation", default=uuid.uuid4)
    created = models.DateTimeField("Created", auto_now_add=True)
    receipt = models.BooleanField("Is receipt", default=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    info = models.TextField("Information", default="")
    currency = models.TextField(
        "Currency",
        default=CurrencyEnum.USD.value,
        choices=enum_to_choices(CurrencyEnum)
    )
    rate = models.DecimalField(
        "Currency rate", default=1, max_digits=12, decimal_places=10
    )
    amount = models.DecimalField("Amount", **money_sum)
    balance = models.DecimalField("Balance", **money_sum)

    class Meta:
        db_table = "payment_wallet_operation"

    def __str__(self) -> str:
        return self.info
