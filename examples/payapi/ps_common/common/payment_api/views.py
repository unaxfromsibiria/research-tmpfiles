import csv
import io
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.shortcuts import HttpResponse
from django.shortcuts import render

from rest_framework import permissions
from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .api import get_actual_exchange_rates
from .api import report_data
from .api import topup_money
from .api import transfer_money
from .models import Wallet


class WalletSerializer(serializers.HyperlinkedModelSerializer):
    """Default wallet data.
    """
    class Meta:
        model = Wallet
        fields = [
            "wallet_id",
            "currency",
            "country",
            "city",
        ]


class OwnerWalletSerializer(serializers.HyperlinkedModelSerializer):
    """Default wallet data.
    """
    class Meta:
        model = Wallet
        fields = [
            "wallet_id",
            "currency",
            "balance",
            "country",
            "city",
            "email",
        ]


class WalletInfoView(APIView):
    """All or owner wallets.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, wallet_id=None, **kwargs):
        """List of wallets.
        """
        if wallet_id:
            serializer = WalletSerializer(
                Wallet.objects.filter(wallet_id=wallet_id),
                context={"request": request},
                many=True
            )
        else:
            serializer = OwnerWalletSerializer(
                request.user, context={"request": request}
            )

        return Response(serializer.data)


class AmountRequestSerializer(serializers.Serializer):
    """Only amount value.
    """
    amount = serializers.DecimalField(
        min_value=Decimal("0.01"), max_digits=10, decimal_places=2
    )


class TopupBalanceView(GenericAPIView):
    """Top up balance.
    """

    serializer_class = AmountRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, **kwargs):
        """Call api system method to top up ballance in user wallet.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {}
        logger = logging.getLogger(settings.DEFAULT_LOGGER_NAME)
        try:
            with transaction.atomic():
                operation = topup_money(
                    request.user.wallet_id,
                    Decimal(serializer.data["amount"])
                )
        except Exception as err:
            if settings.DEBUG:
                data["error"] = f"Problem {err}"

            logger.critical(
                f"Top up error wallet {request.user.wallet_id}: {err}"
            )
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            data["operation"] = operation.hex
            status_code = status.HTTP_200_OK
            logger.debug(f"Correct top up: {operation}")

        return Response(data, status=status_code)


class TransferRequestSerializer(AmountRequestSerializer):
    """Transfer data.
    """
    wallet = serializers.IntegerField(min_value=1)


class TransferApiView(GenericAPIView):
    """Transfer mony to other wallet.
    """

    serializer_class = TransferRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, **kwargs):
        """Call api system method to make transfer.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {}
        logger = logging.getLogger(settings.DEFAULT_LOGGER_NAME)
        # sync request to internal service (todo: use cache if loading)
        exchange_rates = get_actual_exchange_rates(logger)
        if exchange_rates:
            try:
                with transaction.atomic():
                    operation = transfer_money(
                        from_wallet=request.user.wallet_id,
                        to_wallet=serializer.data["wallet"],
                        amount=Decimal(serializer.data["amount"]),
                        actual_retes=exchange_rates
                    )
            except Exception as err:
                if settings.DEBUG:
                    data["error"] = f"Problem {err}"

                logger.critical(
                    f"Transfer from {request.user.wallet_id}: {err}"
                )
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            else:
                data["operation"] = operation.hex
                status_code = status.HTTP_200_OK
                logger.debug(f"Correct transfer: {operation}")
        else:
            data["message"] = "Try again later."
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(data, status=status_code)


class ReportRequestSerializer(serializers.Serializer):
    """Peport period and target.
    """
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    wallet = serializers.IntegerField()
    data_format = serializers.CharField(required=False, allow_null=True)


class OperationReportView(GenericAPIView):
    """Report as html, csv, xml.
    """
    serializer_class = ReportRequestSerializer
    permission_classes = [permissions.AllowAny]  # wtf?

    def get(self, request, **kwargs):
        """Html page or perort files.
        """
        serializer = self.get_serializer(
            data=request.data or request.GET
        )
        serializer.is_valid(raise_exception=True)
        logger = logging.getLogger(settings.DEFAULT_LOGGER_NAME)
        try:
            rows = report_data(**serializer.validated_data)
        except Exception as err:
            logger.error(f"Report error: {err}")
            rows = []

        context = dict(serializer.data)
        context["rows"] = rows

        return render(
            request, template_name="report_page.html", context=context
        )

    def post(self, request, **kwargs):
        """Html page or perort files.
        """
        serializer = self.get_serializer(
            data=request.data or request.GET
        )
        serializer.is_valid(raise_exception=True)
        logger = logging.getLogger(settings.DEFAULT_LOGGER_NAME)
        try:
            rows = report_data(**serializer.validated_data)
        except Exception as err:
            logger.error(f"Report error: {err}")
            rows = []

        data_format = serializer.data.get("data_format")

        if data_format == "xml":
            result = "xml"
            context = dict(serializer.data)
            context["rows"] = rows
            result = render(
                request,
                template_name="report_xml.xml",
                context=context,
                content_type="text/xml"
            )
            result["Content-Disposition"] = (
                f"attachment; filename=report_{serializer.data['wallet']}.xml"
            )

        elif data_format == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC)
            # header
            writer.writerow([
                "dt", "from", "to", "amount", "balance"
            ])
            for row in rows:
                writer.writerow(row)

            result = HttpResponse(buffer.getvalue(), content_type="text/csv")
            result["Content-Disposition"] = (
                f"attachment; filename=report_{serializer.data['wallet']}.csv"
            )
        else:
            status_code = status.HTTP_404_NOT_FOUND
            result = Response(
                f"Unknown format {data_format}", status=status_code
            )

        return result
