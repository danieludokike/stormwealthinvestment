from django.urls import path

from .views import (
    login_view, register_view,
     AccountCreatedView, user_profile_view,
     logout_view, user_account_details,
     deposit_view, process_deposit,
     request_withdrawal, handl_user_mail_admin,
     withdraw_bonus, deposit_from_account_view,
     UpdateWalletView,
)

# THE APPLICATION NAME TO BE ACCESSED IN THE TEMPLATE
app_name = "userdashboard"
urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', register_view, name="register"),
    path("dashboard/", user_profile_view, name="user_profile"),
    path("logout/", logout_view, name="logout"),
    path("signup-successful/", AccountCreatedView.as_view(), name="sign_up_successful"),

    path("account-details/", user_account_details, name="account_details"),
    path("make-deposit/", deposit_view, name="make_deposit"),
    path("make-deposit-from-account/", deposit_from_account_view, name="make-deposit-from-account"),
    path("process-deposit/", process_deposit, name="process_deposit"),
    path("withdraw-balance/", request_withdrawal, name="request_withdraw"),
    path('withdraw-bonus/', withdraw_bonus, name="withdraw_bonus"),
    path("email-admin/", handl_user_mail_admin, name="email_admin"),
    path("update-wallet-addresses/<int:pk>/", UpdateWalletView.as_view(), name="update_wallet"),
]