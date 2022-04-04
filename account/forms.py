from django import forms
from django import forms
from apexapp.models import UserProfile, AdminWalletAddress


class GenericForm(forms.Form):
    """REGISTRATION AND LOGIN FORM WILL INHERIT FROM THIS"""
    username = forms.CharField(max_length=50)
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput,
    )

    class Meta:
        proxy = True


class UserLoginForm(GenericForm):
    """USER LOGIN FORM"""
    pass


class UserRegistrationForm(GenericForm):
    """USER REGISTRATION FORM"""
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=155)
    password2 = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput,
    )
    bitcoin_address = forms.CharField(max_length=150, help_text="Your bitcoin wallet address", required=False)
    bitcoin_cash_address = forms.CharField(max_length=150, help_text="Your bitcoin cash wallet address", required=False)
    ethereum_address = forms.CharField(max_length=150, help_text="Your ethereum wallet address", required=False)
    perfect_money_address = forms.CharField(max_length=150, help_text="Your perfect money wallet address", required=False)
    usdt_trc20_address = forms.CharField(max_length=150, help_text="Your usdt trc20 wallet address", required=False)
    usdt_erc20_address = forms.CharField(max_length=150, help_text="Your usdt erc20 wallet address", required=False)
    bnb_address = forms.CharField(max_length=150, help_text="Your bnb wallet address", required=False)
    payeer_address = forms.CharField(max_length=150, help_text="Your payeer wallet address", required=False)
    check_box = forms.BooleanField(required=True)


class DepositForm(forms.ModelForm):
    """DEPOSIT FORM FOR PAYMENT"""
    class Meta:
        model = UserProfile
        fields = ('plan_type', 'last_coin_paid')


class WalletSelectForm(forms.ModelForm):
    """DEPOSIT FORM FOR PAYMENT"""
    class Meta:
        model = AdminWalletAddress
        fields = ('wallet_type',)