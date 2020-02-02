# only simple cases
import logging
from decimal import Decimal

from django.test import TestCase

from common.payment_api.api import get_actual_exchange_rates
from common.payment_api.api import report_data
from common.payment_api.api import topup_money
from common.payment_api.api import transfer_money
from common.payment_api.models import CurrencyEnum
from common.payment_api.models import Wallet
from common.payment_api.models import WalletOperation


class ApiTransferTestCase(TestCase):
    """Tests for main api methods.
    """
    test_data = {}

    def setUp(self):
        record1 = Wallet.objects.create_user(
            username="testuser1",
            password="testuser1",
            currency=CurrencyEnum.EUR.value,
            balance=1000
        )
        record2 = Wallet.objects.create_user(
            username="testuser2",
            password="testuser2",
            currency=CurrencyEnum.USD.value,
            balance=1000
        )
        self.test_data["wallet_id_1"] = record1.wallet_id
        self.test_data["wallet_id_2"] = record2.wallet_id

    def test_transfer_operation_creating(self):
        """Test main api transfer method.
        """
        assert self.test_data.get("wallet_id_1")
        assert self.test_data.get("wallet_id_2")

        operation_id = transfer_money(
            from_wallet=self.test_data.get("wallet_id_1"),
            to_wallet=self.test_data.get("wallet_id_2"),
            amount=100,
            actual_retes={
                "USD": Decimal(1),
                "EUR": Decimal("1.20052"),
            }
        )

        operations = WalletOperation.objects.filter(
            operation=operation_id
        ).values_list(
            "wallet__wallet_id", "amount", "balance", "receipt"
        )

        assert operation_id
        result = set(map(tuple, operations.iterator()))
        assert result == {
            (self.test_data.get("wallet_id_1"), Decimal("100.00"), Decimal("900.00"), False),  # noqa
            (self.test_data.get("wallet_id_2"), Decimal("120.05"), Decimal("1120.05"), True),  # noqa
        }

        amount = Wallet.objects.filter(
            wallet_id=self.test_data.get("wallet_id_1")
        ).values_list("balance", flat=True).first()
        assert amount == Decimal("900.00")

        amount = Wallet.objects.filter(
            wallet_id=self.test_data.get("wallet_id_2")
        ).values_list("balance", flat=True).first()
        assert amount == Decimal("1120.05")

    def test_topup_operation(self):
        """Test main api topup method.
        """
        assert self.test_data.get("wallet_id_1")

        operation_id = topup_money(
            wallet=self.test_data.get("wallet_id_1"), amount=10
        )

        operations = WalletOperation.objects.filter(
            operation=operation_id
        ).values_list(
            "wallet__wallet_id", "amount", "balance", "receipt"
        )

        assert operation_id
        result = set(map(tuple, operations.iterator()))
        assert result == {
            (self.test_data.get("wallet_id_1"), Decimal("10"), Decimal("1010"), True),  # noqa
        }

        amount = Wallet.objects.filter(
            wallet_id=self.test_data.get("wallet_id_1")
        ).values_list("balance", flat=True).first()
        assert amount == Decimal("1010.00")

    def test_report_data(self):
        """Test main api transfer method.
        """
        assert self.test_data.get("wallet_id_1")
        assert self.test_data.get("wallet_id_2")

        transfer_money(
            from_wallet=self.test_data.get("wallet_id_1"),
            to_wallet=self.test_data.get("wallet_id_2"),
            amount=100,
            actual_retes={
                "USD": Decimal(1),
                "EUR": Decimal("1.20052"),
            }
        )

        operation_id = topup_money(
            wallet=self.test_data.get("wallet_id_1"), amount=10
        )

        dt = WalletOperation.objects.filter(
            operation=operation_id
        ).values_list(
            "created", flat=True
        ).first()

        day = dt.date()
        wallet = self.test_data.get("wallet_id_1")

        result = [
            (row.dt[:10], row.w_from, row.w_to, row.amount, row.balance)
            for row in report_data(
                wallet=wallet,
                start_date=day,
                end_date=day
            )
        ]

        assert result == [
            (day.isoformat(), wallet, self.test_data.get("wallet_id_2"), "- 100.00", Decimal("900.00")),  # noqa
            (day.isoformat(), "-", wallet, "+ 10.00", Decimal("910.00")),  # noqa
        ]

    def test_wrong_rate_request(self):
        """Test wrong url.
        """
        test_data = []
        def fake_critical(*args, **kwargs):
            test_data.append(args)

        logger = logging.getLogger("stdout")
        logger.critical = fake_critical
        with self.settings(RATE_SERVICE_URLS=["http://no.source/url"]):
            result = get_actual_exchange_rates(logger)

        assert not result
        assert test_data == [("No actual exchange rates!",)]
