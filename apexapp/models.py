from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from django.shortcuts import get_object_or_404
from embed_video.fields import EmbedVideoField
from django.contrib.auth.models import User

from datetime import datetime

from account.utils import email_user_deposit, email_user_withdrawal

# ====================CHOICES FOR SELECTING PRICE PLAN NAME AND EARNING RATE=========================================
PLAN_TYPE = (
    ("MINOR", "MINOR"),
    ("PREMIUM", "PREMIUM"),
    ("ULTIMATE", "ULTIMATE"),
    ("MEGA", "MEGA"),
)

COIN_TYPE = (
    ("BITCOIN", "BITCOIN"),
    ("BITCOIN CASH", "BITCOIN CASH"),
    ("ETHEREUM", "ETHEREUM"),
    ("PERFECT MONEY", "PERFECT MONEY"),
    ("USDT TRC20", "USDT TRC20"),
    ("USDT ERC20", "USDT ERC20"),
    ("BNB", "BNB"),
    ("PAYEER", "PAYEER"),
    
)

EARNING_RATE = (
    ("2%", "2%"),
    ("2.5%", "2.5%"),
    ("3%", "3%"),
    ("4%", "4%")
)

WITHDRAW_FROM = (
    ("ACCOUNT BALANCE", "ACCOUNT BALANCE"),
    ("REFERRAL BONUS", "REFERRAL BONUS")
)

STATUS = (
    ("PENDING", "PENDING"),
    ("APPROVED", "APPROVED")
)
# ======================================================================================================


class DepositTransaction(models.Model):
    """RECORDS ALL THE DEPOSITS TRANSACTION DONE BY THE USER"""
    user = models.OneToOneField(User, related_name="user_deposit_transactions", on_delete=models.CASCADE)
    user_amount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True)
    current_balance = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True)
    amount_to_add = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True, help_text="Enter the amount the user deposited. Please do not touch this field")
    referrer_bonus = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True, help_text="Bonus of the referrer. Please do not touch this field")
    amount_to_withdraw = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True, help_text="Current Earning of the user. Please do not touch this field")
    date_deposited = models.DateField(default=datetime.now)
    transaction_referrence = models.CharField(max_length=150, help_text="Leave the transaction referrence as it is. It's use for sending the user an email", null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f"{self.user} ++ ${self.user_amount}"

    def save(self):
        if self.status == "APPROVED" and self.amount_to_add > 0:
            # DEFAULTING AMOUNT TO WITHDRAW TO ZERO AS THIS IS USED TO MONITOR THE CURRENT AMOUNT AVAILABLE FOR WITHDRAWAL
            self.amount_to_withdraw = 0.0

            # SENDING DEPOSIT PROOF TO THE USER
            wallet_ddr = get_object_or_404(UserProfile, user=self.user)
            wallet_ddr = wallet_ddr.wallet_address_used
            user_email = get_object_or_404(User, username=self.user)
            email_user_deposit(self.user, self.transaction_referrence, self.amount_to_add, self.date_deposited, wallet_ddr, user_email.email, self.status)        
        
        # ADDING TO AMOUNT_TO_ADD TO AMOUNT_DEPOSITED
        referrer = None
        if UserProfile.objects.filter(user=self.user).exists():
            user_pr = UserProfile.objects.get(user=self.user)
            referrer = user_pr.referrer

        # ADDING TO AMOUNT_TO_ADD TO AMOUNT_DEPOSITED
        if self.status == "APPROVED":
            self.user_amount = float(self.user_amount) + float(self.amount_to_add)
            self.referrer_bonus = float(self.amount_to_add)*(float(12/100))

            if referrer is not None:
                # MAKING CHANGES TO THE BONUS AND AMOUNT TO ADD
                referrer_bonus = ReferralBonus.objects.get(username=referrer)
                referrer_bonus.accumulated_bonus = float(referrer_bonus.accumulated_bonus) + float(self.amount_to_add)*(float(12/100))
                referrer_bonus.save()
            self.amount_to_add = 0.0

        # SAVING THE CHANGES TO THE RECORD
        if TransactionRecord.objects.filter(transaction_referrence=self.transaction_referrence).exists():
            user_tran_rec = TransactionRecord.objects.filter(transaction_referrence=self.transaction_referrence).order_by("-id").first()
            user_tran_rec.status = self.status
            user_tran_rec.save()

        user_obj = super(DepositTransaction, self).save()
        return user_obj


class WithdrawalTransaction(models.Model):
    """RECORDS ALL TEH WITHDRAWAL TRANSACTIONS DONE BY THE USER"""
    user = models.OneToOneField(User, related_name="user_withdrawal_transactions", on_delete=models.CASCADE, help_text="Select the user here")
    amount_to_withdraw = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, help_text="Enter the amount the user wants to withdraw")
    withdraw_from = models.CharField(max_length=20, choices=WITHDRAW_FROM)
    withdrawal_date =  models.DateField(default=datetime.now)
    transaction_referrence = models.CharField(max_length=150, help_text="Leave the transaction referrence as it is. It's use for sending the user an email", null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f"{self.user} -- ${self.amount_to_withdraw}"

    def save(self):
        """MAKES SOME CHANGES WHEN THE TRANSACTION IS SAVED"""
        # GETTING USER INFO
        wallet_ddr = get_object_or_404(UserProfile, user=self.user)
        wallet_ddr = wallet_ddr.wallet_address_used
        user_email = get_object_or_404(User, username=self.user)
        user_email = user_email.email

        if WithdrawalTransaction.objects.filter(transaction_referrence=self.transaction_referrence).exists():
            user_tran_rec = TransactionRecord.objects.filter(transaction_referrence=self.transaction_referrence).order_by("-id").first()
            user_tran_rec.status = self.status
            user_tran_rec.save()

            if self.status == "APPROVED" and self.withdraw_from == "ACCOUNT BALANCE":
                # username = user_tran_rec.username
                user_deposit_tran = get_object_or_404(DepositTransaction, user=self.user)
                user_deposit_tran.current_balance = float(user_deposit_tran.current_balance) - float(self.amount_to_withdraw)
                user_deposit_tran.amount_to_withdraw = round(float(user_deposit_tran.amount_to_withdraw) + float(self.amount_to_withdraw))
                user_deposit_tran.save()

                # DELETING ALL THE EARNINGS OF THE USER
                UserEarningRecord.objects.filter(username=self.user).delete()
                
                # SENDING EMAIL TO THE USER
                email_user_withdrawal(self.user, self.transaction_referrence, self.amount_to_withdraw, self.withdrawal_date, wallet_ddr, user_email, self.status, "ACC")

            elif self.status == "APPROVED" and self.withdraw_from == "REFERRAL BONUS":
                if ReferralBonus.objects.filter(username=self.user).exists():
                    user_bonus = ReferralBonus.objects.get(username=self.user)
                    user_bonus.accumulated_bonus = float(user_bonus.accumulated_bonus) - float(self.amount_to_withdraw)
                    user_bonus.save()

                # SENDING EMAIL TO THE USER
                email_user_withdrawal(self.user, self.transaction_referrence, self.amount_to_withdraw, self.withdrawal_date, wallet_ddr, user_email, self.status, "REFF")


        obj = super(WithdrawalTransaction, self).save()
        return obj 

class UserProfile(models.Model):
    """RECORDS THE USER ACCOUNT DETAILS"""
    user = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE, default="MINOR")
    earning_rate = models.CharField(max_length=10, choices=EARNING_RATE, default="2%")
    referrer = models.CharField(max_length=50, null=True, blank=True)
    wallet_address_used = models.CharField(max_length=150, help_text="User wallet address used for last withdrawal transaction", null=True, blank=True)
    bitcoin_address = models.CharField(max_length=150, help_text="User bitcoin wallet address for payment", null=True, blank=True)
    bitcoin_cash_address = models.CharField(max_length=150, help_text="User bitcoin cash wallet address for payment", null=True, blank=True)
    ethereum_address = models.CharField(max_length=150, help_text="User Ethereum wallet address for payment", null=True, blank=True)
    perfect_money_address = models.CharField(max_length=150, help_text="User perfect money wallet address for payment", null=True, blank=True)
    usdt_trc20_address = models.CharField(max_length=150, help_text="User usdt trc20 wallet address for payment", null=True, blank=True)
    usdt_erc20_address = models.CharField(max_length=150, help_text="User usdt erc20 wallet address for payment", null=True, blank=True)
    bnb_address = models.CharField(max_length=150, help_text="User BNB wallet address for payment", null=True, blank=True)
    payeer_address = models.CharField(max_length=150, help_text="User PAYEER wallet address for payment", null=True, blank=True)
    last_coin_paid = models.CharField(max_length=50, choices=COIN_TYPE, help_text="The coin selected by the user during the last payment", null=True, blank=True, default="BITCOIN")
    class Meta:
        ordering = ['user']

    def __str__(self):
        return f"{self.user}: {self.plan_type}"


class ReferralBonus(models.Model):
    """STORES THE REFERRAL BONUS OF EACH USER"""
    username = models.CharField(max_length=50, unique=True)
    total_person_referred = models.PositiveIntegerField(default=0)
    accumulated_bonus = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True, help_text="User can only get bonus when those they referred pay")

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ++ ${self.accumulated_bonus}"


class TransactionRecord(models.Model):
    """RECORDS ALL THE USER TRANSACTIONS"""
    username = models.CharField(max_length=50)
    amount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50)
    transaction_referrence = models.CharField(max_length=150, unique=True)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username}: {self.transaction_referrence}"


class AdminWalletAddress(models.Model):
    wallet_type = models.CharField(max_length=50, choices=COIN_TYPE, default="BITCOIN", unique=True)
    wallet_address = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.wallet_type}: {self.wallet_address}"


class Top10Deposit(models.Model):
    """RECORDS THE TOP TEN DEPOSITS OF USER"""
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['username']

    def  __str__(self):
        return f"{self.username}"


class Top10Withdrawal(models.Model):
    """RECORDS THE TOP TEN DEPOSITS OF USER"""
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['username']

    def  __str__(self):
        return f"{self.username}"


# YOUTUBE VIDEO UPLOAD
class CompanyYoutubeTubeVideo(models.Model):
    title = models.CharField(max_length=50)
    video_url = EmbedVideoField()  # same like models.URLField()

    class Meta:
        ordering = ['-id']
        pass

    def __str__(self):
        return f"{self.title}"


# MODEL FOR SENDING EMAIL TO USERS
class EmailUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    message = models.TextField(max_length=1000)

    def save(self):
        user = User.objects.get(username=self.user)
        user_email = user.email

        send_mail(
        self.title,
        self.message,
        settings.EMAIL_HOST_USER,
        [user_email,]
        )
        return


class UserEarningRecord(models.Model):
    """RECORDS THE  EARNING OF EACH USER"""
    username = models.CharField(max_length=50)
    amount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    earning = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    percentage = models.CharField(max_length=10, default="2%")
    date = models.DateField(default=datetime.now) # For auto date add

    def __str__(self):
        return f"{self.username} -> {self.date}"


