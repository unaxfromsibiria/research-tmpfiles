from django.contrib import admin

from .models import Wallet
from .models import WalletOperation


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin class for Wallet.
    """

    list_display = (
        "wallet_id",
        "created",
        "currency",
        "balance",
    )

    list_display_links = (
        "wallet_id",
    )

    list_filter = (
        "currency",
    )


@admin.register(WalletOperation)
class WalletOperationAdmin(admin.ModelAdmin):
    """Admin class for WalletOperation.
    """

    list_display = (
        "created",
        "info",
        "operation",
        "amount",
        "receipt",
    )

    list_display_links = (
        "created",
    )

    list_filter = (
        "currency",
        "receipt",
    )
