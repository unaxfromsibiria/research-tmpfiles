from django.urls import path

from .views import OperationReportView
from .views import TopupBalanceView
from .views import TransferApiView
from .views import WalletInfoView

urlpatterns = [
    path("wallet/", WalletInfoView.as_view(), name="wallet"),
    path("wallet/<int:wallet_id>/", WalletInfoView.as_view(), name="wallet-info"),  # noqa
    path("topup/", TopupBalanceView.as_view(), name="wallet-topup"),
    path("transfer/", TransferApiView.as_view(), name="wallet-transfer"),
    path("operations/", OperationReportView.as_view(), name="report-main"),  # noqa
]
