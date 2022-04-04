from django.contrib import admin

from .models import (
    DepositTransaction, WithdrawalTransaction,
    AdminWalletAddress, UserProfile,
    Top10Deposit, Top10Withdrawal,
    CompanyYoutubeTubeVideo, ReferralBonus,
    TransactionRecord,EmailUser, UserEarningRecord
)

# ADDING SEARCH FIELD
class DepositTransactionAdmin(admin.ModelAdmin):
    search_fields=("user__username",)


# ADDING SEARCH FIELD
class WithdrawalTransactionAdmin(admin.ModelAdmin):
    search_fields=("user__username",)


# ADDING SEARCH FIELD
class UserProfileAdmin(admin.ModelAdmin):
    search_fields=("user__username",)



admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(DepositTransaction, DepositTransactionAdmin)
admin.site.register(WithdrawalTransaction, WithdrawalTransactionAdmin)
admin.site.register(ReferralBonus)
admin.site.register(TransactionRecord)
admin.site.register(AdminWalletAddress)
admin.site.register(Top10Deposit)
admin.site.register(Top10Withdrawal)
admin.site.register(CompanyYoutubeTubeVideo)
admin.site.register(EmailUser)
admin.site.register(UserEarningRecord)

admin.site.site_header = "APEX GRANT INVESTMENT ADMINISTRATOR"
admin.site.site_title = "Apexgrantinvestment"
admin.site.site_url = "apexgrantinvestment.com"

