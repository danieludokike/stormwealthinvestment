# HEROKU MAIL FOR THIS ACCOUNT IS HEROKUHOST50@GMAIL.COM
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import fields
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView, UpdateView
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .forms import UserLoginForm, UserRegistrationForm, DepositForm, WalletSelectForm

from .decorators import un_authenticated_users

from apexapp.models import (
    UserProfile, DepositTransaction,
    WithdrawalTransaction,
    ReferralBonus, TransactionRecord,
    AdminWalletAddress, UserEarningRecord,
)

from .utils import (
    is_empty, is_email_valid,
    is_equal, is_email_taken,
    is_username_taken, is_username_valid,
    is_safe, validate_wallet_addr, 
    redirect_to_singup_page,
    # EMAIL FUNCTIONS IN UTILS
    email_user_registration, email_referrer,
    email_admin, add_admin_mail
)

# ==================================================================================================
import string    
import random

def generate_ref():
    """RETURN RANDOM GENERATED CHARATER TO BE USED AS TRANSACTION BATCH"""
    return str(''.join(random.choices(string.ascii_uppercase + string.digits + str(datetime.now()), k = 60)))


# FUNCTION TO HANDLE TO HANDLE ADDING USER EARNING TO RECORD
def add_user_earnings(username, amount, earning, percentage, date):
    # PERFORMING ADDITION OF USER EARNING RECORD IF ANY
    user_earn = None
    if UserEarningRecord.objects.filter(username=username).exists():
        user_earn = get_list_or_404(UserEarningRecord, username=username)
        earning_dates = [str(d.date) for d in user_earn]
        if str(date) in earning_dates:
            pass
        else:
            user_earn = UserEarningRecord(
            username=username,
            amount=amount,
            earning=earning,
            percentage=percentage,
            date=date,
            )
            user_earn.save()
    else:
        user_earn = UserEarningRecord(
        username=username,
        amount=amount,
        percentage=percentage,
        date=date,
        )
        user_earn.save()

# =================================================================================================


@un_authenticated_users
def register_view(request):
    """HANDLES USER REGISTRATION"""
    template = "account/signup.html"
    if request.method == "POST":
        registration_form = UserRegistrationForm(request.POST)
        first_name = request.POST.get("first_name", None)
        last_name = request.POST.get("last_name", None)
        username = request.POST.get("username", None)
        email = request.POST.get("email", None)
        password = request.POST.get("password", None)
        password2 = request.POST.get("password2", None)
        bitcoin_address = request.POST.get("bitcoin_address", None)
        bitcoin_cash_address = request.POST.get("bitcoin_cash_address", None)
        ethereum_address = request.POST.get("ethereum_address", None)
        stellar_address = request.POST.get("stellar_address", None)
        litecoin_address = request.POST.get("litecoin_address", None)

        """CHECKING IF THE FIELD IS EMPTY"""
        if is_empty(first_name, last_name, username, email, password, password2):
            messages.error(request, "Please fill out fields with *!!")
            return redirect_to_singup_page(request, template, registration_form)

        """CHECKING IF THE CHECK BOX IS CHECKED"""
        if not request.POST.get("check_box"):
            messages.error(request, "Accept Terms and Conditions to signup")
            return redirect_to_singup_page(request, template, registration_form)

        """CHECKING IF THE USERNAME IS IN VALID FORMAT"""
        if not is_username_valid(username):
            messages.error(request, "This username is invalid. Only letters, numbers and underscores are allowed")
            return redirect_to_singup_page(request, template, registration_form)

        """CHECKING IF THE USERNAME ALREADY EXISTS IN THE DATABASE"""
        if is_username_taken(username):
            messages.error(request, "This username is already taken by another user")
            return redirect_to_singup_page(request, template, registration_form)

        """CHECKING IF THE EMAIL ADDRESS IS VALID"""
        if not is_email_valid(email):
            messages.error(request, "Invalid Email Address. Valid email looks like \"you@domain.com\"")
            return redirect_to_singup_page(request, template, registration_form)

        """CHKING IF THE EMAIL ADDRESS ALREADY EXISTS"""
        if is_email_taken(email):
            messages.error(request, "This email address is already in use by another user")
            return redirect_to_singup_page(request, template, registration_form)

        """CHECKING IF THE PASSWORDS MATCHES"""
        if not is_equal(password, password2):
            messages.error(request, "The two passwords do not match!!")
            return redirect_to_singup_page(request, template, registration_form)

        if not is_safe(password):
            messages.error(request, "Password length must be minimum of 8, and must contain letters and numbers only!!")
            return redirect_to_singup_page(request, template, registration_form)

        # """VALIDATIN THE WALLET ADDRESS"""
        # if not validate_wallet_addr(wallet_address):
        #     messages.error(request, "A valid wallet address is required. Wallet address is between 8 and above of characters")
        #     return redirect_to_singup_page(request, template, registration_form)

        # CREATING A USER
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        print(bitcoin_address)
        # CREATING USER PROFILE
        user_profile = UserProfile(user=user)
        user_profile.plan_type = "GENERAL"
        user_profile.earning_rate = "1.9%"
        user_profile.bitcoin_address = bitcoin_address
        user_profile.bitcoin_cash_address = bitcoin_cash_address
        user_profile.ethereum_address = ethereum_address
        user_profile.stellar_address = stellar_address
        user_profile.litecoin_address = litecoin_address


        # CREATING USER TRANSACTIONS
        user_transaction = DepositTransaction(user=user)
        user_transaction.user_amount = 0.00
        user_transaction.date_deposited = datetime.now()
        user_transaction.current_balance = 0.0
        user_transaction.transaction_referrence = generate_ref()  # CALLING THE FUNCTION TO GENERATE A RANDOM TEXT
        user_transaction.status = "PENDING"
        # user_transaction.plan_type = "STARTER"

        # CHECKING IF THE REFERRER USERNAME EXISTS
        if request.session.get("referrer", None):
            # CREATING USER PROFILE
            user_profile.referrer = request.session["referrer"]
            # INCREMENTING THE NUMBER OF PERSON REFERRED BY THE REFERRER
            user_ref = ReferralBonus.objects.filter(username=request.session["referrer"]).exists()
            if user_ref:
                user_ref = ReferralBonus.objects.get(username=request.session["referrer"])
                user_ref.total_person_referred += 1
                user_ref.save() # SAVING BACK THE TOTAL PERSON REFERRED
            else:
                ReferralBonus.objects.create(username=request.session["referrer"], total_person_referred=1, accumulated_bonus=0.0)

            user_ref = ReferralBonus.objects.get(username=request.session["referrer"])
            # SENDING EMAIL TO THE REFERRER
            referrer_email = User.objects.get(username=request.session["referrer"]).email
            email_referrer(referrer_email, username, user_ref.total_person_referred)

            del request.session["referrer"]
        # SAVING USER ,PROFILE AND TRANSACTION
        user.save()
        user_profile.save()
        user_transaction.save()

        # SENDING EMAIL TO USER
        email_user_registration(username, password, email)

        return render(request, "account/registration_success.html", {"username": username})

    # REQUEST GET
    registration_form = UserRegistrationForm()
    context = {
        "form": registration_form,
    }
    return render(request, template, context)


class AccountCreatedView(TemplateView):
    template_name = "account/registration_success.html"



@un_authenticated_users
def login_view(request):
    """HANDLES USER LOGIN FUNCTIONALITY"""
    if request.method == "POST":
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)

        # GETTING THE USERNAME AND PASSWORD
        user = auth.authenticate(username=username, password=password)     

        if user is not None:
            auth.login(request, user)
            return redirect("userdashboard:user_profile")
        messages.error(request, "Invalid username or password. Both fields may be case sensitive")
        return redirect("userdashboard:login")

    form = UserLoginForm(request.GET)
    return render(request, "account/login.html", {"form": form})


def logout_view(request):
    """HANDLES USER LOGOUT"""
    auth.logout(request)
    messages.info(request, "Your session has been cleared. You need to login again")
    return redirect("userdashboard:login")


@login_required(login_url="userdashboard:login")
def user_profile_view(request):
    """USER'S DASHBOARD"""
    if request.user.is_superuser:
        messages.success(request, f"Welcom, {request.user}")
        return redirect("/admin/")

    if request.user.is_authenticated:
        template = "account/user_dashboard.html"

        user = User.objects.get(id=request.user.id)
        deposit_transactions = DepositTransaction.objects.get(user=user)

        # GETTING THE CURRENT AMOUNT OF THE USER THAT'S AVAILABLE FOR WITHDRAWAL
        aval_amount = float(deposit_transactions.amount_to_withdraw)
        
        tran_status = deposit_transactions.status
        
        users_detail = UserProfile.objects.get(user=user)

        # for user_dt in users_details:
        rate = users_detail.earning_rate.replace("%", "")
        plan_type = users_detail.plan_type

        today = datetime.now().date() # THE CURRENT DATE
        withdrawal_msg = "No current deposit accumulating!"
        
        deposit = round(float(deposit_transactions.user_amount), 2) # THE CURRENT AMOUNT DEPOSITED BY THE USER
        deposit_transactions.current_balance = deposit + round((7 * (round((float(rate)/100) * deposit, 2)) - aval_amount), 2)
        deposit_transactions.save()

        balance = deposit_transactions.current_balance

        payment_date = deposit_transactions.date_deposited # DATE OF PAYMENT
        
        days = (today - payment_date).days
              # MAKING CALCULATION AND PRINTING TO USER EARNING RECORD
        if int(days) < 7 and deposit > 0:
            deposit_transactions.current_balance = round((deposit + (int(days) * ( (float(rate)/100) * deposit)) - aval_amount), 2)
            deposit_transactions.save()
            balance = deposit_transactions.current_balance
            withdrawal_msg = f"You have {7-int(days)} days remaining for withdrawal"

        elif days == 7 and deposit > 0:
            deposit_transactions.current_balance = round((deposit + (int(days) * ( (float(rate)/100) * deposit)) - aval_amount), 2)
            deposit_transactions.save()
            balance = deposit_transactions.current_balance
            withdrawal_msg = f"Your balance is ready for withdrawal."

        elif days > 7 and deposit > 0:
            withdrawal_msg = f"Your balance is ready for withdrawal."
        

        context = {
            # "user_transactions":transactions,
            "referrer": UserProfile.objects.get(user=request.user).referrer,
            "deposit": deposit,
            "balance": balance, 
            "withdrawal_msg": withdrawal_msg,
            "days": days,
            "plan_type":plan_type,
            "rate": rate,
            "id": users_detail.id,
             }
        return render(request, template, context)
    messages.info(request, "Authentication is required to access the user profile")
    return redirect("bitapp:login")


@login_required(login_url="userdashboard:login")
def user_account_details(request):
    """RECORDS ALL THE TRANSACTIONS DONE BY THE USER"""
    if request.user.is_authenticated:
        template = "account/account-details.html"
        user = User.objects.get(id=request.user.id)
        deposit_transactions = DepositTransaction.objects.get(user=user)
                
        users_detail = UserProfile.objects.get(user=user)

        # for user_dt in users_details:
        rate = users_detail.earning_rate.replace("%", "")

        today = datetime.now().date() # THE CURRENT DATE
        
        deposit = round(float(deposit_transactions.user_amount), 2) # THE CURRENT AMOUNT DEPOSITED BY THE USER
        deposit_transactions.current_balance = deposit + (7 * ( (float(rate)/100) * deposit))
        deposit_transactions.save()

        payment_date = deposit_transactions.date_deposited # DATE OF PAYMENT
        
        days = (today - payment_date).days
        for i in range(int(days)+1):
            if i > 7:
                break;
            else:
                if i == 0 and deposit > 0:
                    earning = int(0) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(0)))
                if i == 1 and deposit > 0:
                    earning = int(1) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(1)))
                if i == 2 and deposit > 0:
                    earning = int(2) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(2)))
                if i == 3 and deposit > 0:
                    earning = int(3) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(3)))
                if i == 4 and deposit > 0:
                    earning = int(4) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(4)))
                if i == 5 and deposit > 0:
                    earning = int(5) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(5)))
                if i == 6 and deposit > 0:
                    earning = int(6) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(6)))
                if i == 7 and deposit > 0:
                    earning = int(7) * ((float(rate)/100) * (deposit))
                    add_user_earnings(request.user, deposit, earning, rate, payment_date+timedelta(days=int(7)))
        # FIRST 20 TRANSACTIONS OF THE USER
        transactions = TransactionRecord.objects.filter(username=request.user).order_by("-id")[:20]

        # EARNING TRANSACTION HISTORY OF THER USER
        earnings = UserEarningRecord.objects.filter(username=request.user).order_by("-date")[:40]

        # GETTING AND SAVING USER REFERREES
        referrer_bonus = None
        if ReferralBonus.objects.filter(username=request.user).exists():
            referrer_bonus = get_object_or_404(ReferralBonus, username=request.user)
            
        user = User.objects.get(id=request.user.id)
        users_detail = UserProfile.objects.get(user=user)

        context = {
            "each_user_bonus_for_referrer": UserProfile.objects.filter(referrer=request.user),
            "transactions":transactions,
            "referral_bonus": referrer_bonus,
            "id": users_detail.id,
            "earnings": earnings,
             }
        return render(request, template, context)
    messages.info(request, "Authentication is required to access the user profile")
    return redirect("userdashboard:login")


@login_required(login_url="userdashboard:login")
def deposit_view(request):
    """DISPLAYS THE DEPOSIT HTML"""
    template = "account/deposit.html"
    if request.method == "POST":
        deposit_form = DepositForm(request.POST)
        plan_type = request.POST.get("plan_type", None)
        coin_type = request.POST.get("last_coin_paid", None)
        amount = request.POST.get("amount", None).strip()

        plan_types = ["GENERAL", "TRILLER", "PRO", "EXPERT"]
        COIN_TYPE = ["BITCOIN", "BITCOIN CASH", "ETHEREUM", "STELLAR", "LITECOIN"]

        # CHECKING IF THE COIN SELECTED IS THE RIGHT ONE
        if coin_type not in COIN_TYPE:
            messages.error(request, "Please select either bitcoin, perfect money or ethereum")
            return render(request, template, {"deposit_form": deposit_form})

        # CREATING A SESSION FOR COIN_TYPE
        request.session["coin_type"] = coin_type

        # CHECKING FOR ERRORS IN THE INPUT VALUES
        if plan_type not in plan_types:
            messages.error(request, "Please select an appropriate plan!")
            return render(request, template, {"deposit_form": deposit_form})

        try:
            amount = round(float(amount), 2)
        except:
            messages.error(request, "Enter the amount as digits only!")
            return render(request, template, {"deposit_form": deposit_form})
        
        if plan_type.strip() == plan_types[0]:
            if float(amount) < 100 or float(amount) > 999:
                messages.error(request, f"Please enter appropriate amount. {plan_types[0]} PLAN deposit range: [$100 - $999]")
                return render(request, template, {"deposit_form": deposit_form})

        if plan_type.strip() == plan_types[1]:
            if float(amount) < 1_000 or float(amount) > 4_999:
                messages.error(request, f"Please enter appropriate amount. {plan_types[1]} PLAN deposit range: [$1,000 - $4,999]")
                return render(request, template, {"deposit_form": deposit_form})

        if plan_type.strip() == plan_types[2]:
            if float(amount) < 5_000 or float(amount) > 9_999:
                messages.error(request, f"Please enter appropriate amount. {plan_types[2]} PLAN deposit range: [$5, 000 -$9,999]")
                return render(request, template, {"deposit_form": deposit_form})

        if plan_type.strip() == plan_types[3]:
            if float(amount) < 10_000:
                messages.error(request, f"Please enter appropriate amount. {plan_types[3]} PLAN deposit range: [$10, 000 AND ABOVE)")
                return render(request, template, {"deposit_form": deposit_form})

        if plan_types[0] == plan_type:
            percentage = "1.9"
        elif plan_types[1] == plan_type:
            percentage = "2.8"
        elif plan_types[2] == plan_type:
            percentage = "3.9"
        else:
            percentage = "5.5"
            
        # IF ALL THE INPUTS ARE CORRECT FOR EACH PLAN PROCEED TO PROCESS PAYMENT
        context = {
            "current_amount": DepositTransaction.objects.get(user=request.user).user_amount,
            "plan_type":plan_type,
            "amount": amount,
            "percentage": percentage,
            "coin_type": coin_type,
        }
        return render(request, "account/confirm-deposit.html", context)

    # REQUEST METHOD IS GET
    deposit_form = DepositForm()
    context = {
        "deposit_form":deposit_form,
    }
    return render(request, template, context)


@login_required(login_url="userdashboard:login")
def deposit_from_account_view(request):
    """Makes a deposite from the user current account balance"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user_deposit_tran = get_object_or_404(DepositTransaction, user=request.user)

    user_earn_rate = user_profile.earning_rate
    acc_amount = round(float(user_deposit_tran.current_balance), 2)

    today = datetime.now().date() # THE CURRENT DATE
    payment_date = user_deposit_tran.date_deposited
    
    can_withdraw = False
    plan_type = "GENERAL"
    amount = "0.0"
    percentage = "1.9%"

    days = (today - payment_date).days
    # CHECKING IF THE BALANCE IS LESS THAN THE MINIMUM AMOUNT, 100 USD
    if acc_amount < 100:
        messages.error(request, f"You don't have any active balance accumulating or your balance is less than the minimum amount, $100.")
        return redirect("userdashboard:make_deposit")

    if days >= 7 and user_deposit_tran.status == "APPROVED":
        if acc_amount >= 100:
            can_withdraw = True
            plan_type = user_profile.plan_type
            amount = acc_amount
            percentage = user_earn_rate
    else:
        messages.error(request, f"Your active investment has not reached the date to re-invest. Your payment was made on {payment_date}")
        return redirect("userdashboard:make_deposit")
    
    
    if request.method == "POST":
        coin_type = "BITCOIN" if not request.session.get("coin_type") else request.session.get("coin_type")

        plan_type = request.POST.get("plan_type", None)
        amount = request.POST.get("amount", None)
        percentage = request.POST.get("percentage", None).strip().replace("%", "")

        print(plan_type, amount, percentage)

        try:
            amount = round(float(amount), 2)
            per_check = float(percentage)
        except:
            return HttpResponse("<h4 style='color: red;'>You did something wrong. Please start the process again.</h4>")
        

        if plan_type not in ["GENERAL", "TRILLER", "PRO", "EXPERT"]:
            return HttpResponse("<h4 style='color: red;'>You did something wrong. Please start the process again.</h4>")
        

        # SENDING EMAIL TO THE ADMIN
        admin_emails = add_admin_mail()
        send_mail(
        f"{request.user} Re-invested his balance",
        f"User, {request.user} has re-invested his investment: Amount: ${amount}, Plan Type: {plan_type}, Earning Rate: {percentage}." +
        "Do check if this username '{request.user} exists in your admin dashboard",
        settings.EMAIL_HOST_USER,
        admin_emails
        )
        
        # SENDING EMAIL TO USER WHEN DEPOSIT IS RE-INVESTED PROCESS IS INITIATED
        send_mail(
        f"Balance Re-invested",
        f"Hey {request.user}!! did you re-invested your balance? If yes, disregard this message. Amount: ${amount}. Take action now by contacting the admin if you did not initiated this process!!",
        settings.EMAIL_HOST_USER,
        [request.user.email]
        )


        # SAVING THE USER DEPOSIT TO THE TRANSACTION RECORDS
        user_tran = get_object_or_404(DepositTransaction, user=request.user)
        
        tran_ref = generate_ref()
        # SAVING THE USER TRANSACTION
        TransactionRecord.objects.create(
            username=request.user, amount=amount,
            transaction_type="DEPOSIT", transaction_referrence=tran_ref,
            date = datetime.now(), status="APPROVED"
            )

        # UPDATING TRANSACTION
        # HERE, SETTING THE AMOUNT TO ADD TO BE ZERO STOPS THE REFERRAL BONUS NOT TO BE ADDED WHEN RE-INVESTING
        user_tran.current_balance = float(user_tran.current_balance) - amount
        user_tran.user_amount = amount
        user_tran.amount_to_add = 0.0
        user_tran.date_deposited = datetime.now()
        user_tran.transaction_referrence = tran_ref
        user_tran.amount_to_withdraw = 0.0
        user_tran.status="APPROVED"
        # SAVING ALL CHANGES
        user_tran.save()

        messages.info(request, "You payment Record has been updated successfully. You will receive your invoice shortly!!")
        return redirect("userdashboard:account_details")

    context = {
            "plan_type":plan_type,
            "amount": amount,
            "percentage": percentage,
            "can_withdraw": can_withdraw,
    }
    return render(request, "account/deposit_from_account.html", context)


@login_required(login_url="userdashboard:login")
def process_deposit(request):
    """PROCESS THE DEPOSIT AFTER CONFIRMATION"""
    if request.method == "POST":
        template = "account/admin-wallet.html"
        wallet_type = request.session.get("coin_type")
        
        if wallet_type == "BITCOIN":
            coin_type_style="bitcoin"
            admin_wallet = AdminWalletAddress.objects.get(wallet_type="BITCOIN").wallet_address
        elif wallet_type == "BITCOIN CASH":
            coin_type_style = "bitcoincash"
            admin_wallet = AdminWalletAddress.objects.get(wallet_type="BITCOIN CASH").wallet_address
        elif wallet_type == "ETHEREUM":
            coin_type_style = "ethereum"
            admin_wallet = AdminWalletAddress.objects.get(wallet_type="ETHEREUM").wallet_address
        elif wallet_type == "STELLAR":
            coin_type_style = "stellar"
            admin_wallet = AdminWalletAddress.objects.get(wallet_type="STELLAR").wallet_address
        elif wallet_type == "LITECOIN":
            coin_type_style = "litecoin"
            admin_wallet = AdminWalletAddress.objects.get(wallet_type="LITECOIN").wallet_address
        else:
            return HttpResponse("<h4>You did something wrong. Please start the process again.</h4>")

        plan_type = request.POST.get("plan_type", None)
        amount = request.POST.get("amount", None).strip().strip()
        percentage = request.POST.get("percentage", None).strip()

        try:
            amount = round(float(amount), 2)
            per_check = float(percentage)
        except:
            return HttpResponse("<h4>You did something wrong. Please start the process again.</h4>")

        if plan_type not in ["GENERAL", "TRILLER", "PRO", "EXPERT"]:
            return HttpResponse("<h4>You did something wrong. Please start the process again.</h4>")

        # SAVING THE WALLET ADDRESS USED FOR THE TRANSACTION
        user_profile = get_object_or_404(UserProfile, user=request.user)

        COINS = ["BITCOIN", "BITCOIN CASH", "ETHEREUM", "STELLAR", "LITECOIN"]
        if wallet_type not in COINS:
            messages.error(request, "Please select the wallet address for transaction")
            return redirect("userdashboard:request_withdraw")
            
        user_profile = get_object_or_404(UserProfile, user=request.user)
        
        # GETTING THE WALLET ADDRESS OF THER USER WHERE HE/SHE WANTS TO PAY
        if wallet_type == COINS[0]:
            # GETTING THE WALLET ADDRESS THE USER WANTS WANTS THE COIN TO BE SENT TO
            user_wallet_address = user_profile.bitcoin_address
        if wallet_type == COINS[1]:
            user_wallet_address = user_profile.bitcoin_cash_address
        if wallet_type == COINS[2]:
            user_wallet_address = user_profile.ethereum_address
        if wallet_type == COINS[3]:
            user_wallet_address = user_profile.stellar_address
        if wallet_type == COINS[4]:
            user_wallet_address = user_profile.litecoin_address

        # CHECKING IF THE WALLET ADDRESS IS NONE OR INVALID
        # profile_id = UserProfile.objects.get(user=request.user).id
        # if user_wallet_address is None:
        #     wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
        #     messages.error(request, f"Your {wallet_type} wallet address was not found. please update your wallet addresses for you to withdraw through it.")
        #     return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
        
        # # CHECKING IF THE WALLET ADDRESS IS VALID
        # if len(user_wallet_address) < 5:
        #     wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
        #     messages.error(request, f"Your {wallet_type} wallet address seems incomplete, valid wallet address ranges from 8 and above of character. Please update your wallet addresses")
        #     return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
            
        # SAVING THE LATEST WALLET ADDRESS USED FOR TRANSACTION
        user_profile.wallet_address_used = user_wallet_address
        user_profile.save()

        # SENDING EMAIL TO THE ADMIN
        email_admin(request.user, amount, plan_type, str(per_check)+'%'+ f" CRYPTOCURRENCY: {wallet_type}")
       
        # SENDING EMAIL TO USER WHEN DEPOSIT PROCESS IS INITIATED
        send_mail(
        f"Deposit Process Initiated",
        f"Hey {request.user}!! you have initiated a deposit; Amount: ${amount}, Plan Type: {plan_type}, Earning Rate: {percentage}%." +
        f"Make sure you make the actual amount of ${amount}. \n Pay to this wallet address: {admin_wallet}. \n If you are not aware of the action, contact the admin now",
        settings.EMAIL_HOST_USER,
        [request.user.email]
        )

        # EMAIL REFERRER IF ANY
        if UserProfile.objects.filter(user=request.user).exists():
            UserProfile.objects.filter(user=request.user).update(plan_type=plan_type, earning_rate=str(per_check)+'%', last_coin_paid=wallet_type)
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.referrer:
                referrer = user_profile.referrer
                referrer_email = User.objects.get(username=referrer).email
                send_mail(
                    "Referree Payment Process Initiated",
                    f"Your referree, {request.user} has iniated payment of ${amount}. The bonous will be added to your bounus balance when admin approves this payment. Do check your bonus balance.",
                    settings.EMAIL_HOST_USER,
                    [referrer_email]
                )
       

        # SAVING THE USER DEPOSIT TO THE TRANSACTION RECORDS
        user_tran = get_object_or_404(DepositTransaction, user=request.user)
        
        tran_ref = generate_ref()
        # SAVING THE USER TRANSACTION
        TransactionRecord.objects.create(
            username=request.user, amount=amount,
            transaction_type="DEPOSIT", transaction_referrence=tran_ref,
            date = datetime.now(), status="PENDING"
            )

        # UPDATING TRANSACTION
        user_tran.amount_to_add = amount
        # user_tran.date_deposited = datetime.now()
        user_tran.transaction_referrence = tran_ref
        user_tran.status="PENDING"
        # SAVING ALL CHANGES
        user_tran.save()

        return render(request, template, {"admin_wallet":admin_wallet, "amount":amount, "style": coin_type_style})
    return HttpResponse("<h4>Sorry, Only POST request is allowed!!</h4>")


@login_required(login_url="userdashboard:login")
def request_withdrawal(request):
    """HANDLE WITHDRAWAL REQUEST"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user_deposit_tran = get_object_or_404(DepositTransaction, user=request.user)

    user_earn_rate = user_profile.earning_rate.replace("%", "")
    acc_amount = round(float(user_deposit_tran.current_balance), 2)
    user_amount = round(float(user_deposit_tran.user_amount), 2)
    aval_amount = float(acc_amount - user_amount)

    today = datetime.now().date() # THE CURRENT DATE
    payment_date = user_deposit_tran.date_deposited
    
    days = (today - payment_date).days
    if days >= 7 and user_deposit_tran.status == "APPROVED":
        if request.method == "POST":
            amount_to_withdraw = request.POST.get("amount", None).strip()
            wallet_type = request.POST.get("wallet_type", None)

            COINS = ["BITCOIN", "BITCOIN CASH", "ETHEREUM", "STELLAR", "LITECOIN"]
            if wallet_type not in COINS:
                messages.error(request, "Please select the wallet address for transaction")
                return redirect("userdashboard:request_withdraw")
            
            user_profile = get_object_or_404(UserProfile, user=request.user)
            
            # GETTING THE WALLET ADDRESS OF THER USER WHERE HE/SHE WANTS TO PAY
            if wallet_type == COINS[0]:
                # GETTING THE WALLET ADDRESS THE USER WANTS WANTS THE COIN TO BE SENT TO
                user_wallet_address = user_profile.bitcoin_address
            if wallet_type == COINS[1]:
                user_wallet_address = user_profile.bitcoin_cash_address
            if wallet_type == COINS[2]:
                user_wallet_address = user_profile.ethereum_address
            if wallet_type == COINS[3]:
                user_wallet_address = user_profile.stellar_address
            if wallet_type == COINS[4]:
                user_wallet_address = user_profile.litecoin_address

            # CHECKING IF THE WALLET ADDRESS IS NONE OR INVALID
            profile_id = UserProfile.objects.get(user=request.user).id
            if user_wallet_address is None:
                wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
                messages.error(request, f"Your {wallet_type} wallet address was not found. please update your wallet addresses for you to withdraw through it.")
                return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
            
            # CHECKING IF THE WALLET ADDRESS IS VALID
            if len(user_wallet_address) < 5:
                wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
                messages.error(request, f"Your {wallet_type} wallet address seems incomplete, valid wallet address ranges from 8 and above of character. Please update your wallet addresses")
                return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
                
            # SAVING THE LATEST WALLET ADDRESS USED FOR TRANSACTION
            user_profile.wallet_address_used = user_wallet_address
            user_profile.save()

            try:
                amount_to_withdraw = round(float(amount_to_withdraw), 2)
            except ValueError:
                messages.error(request, "Please enter amount as number")
                return redirect("userdashboard:request_withdraw")

            # CHECKING THE AMOUNT THE USER WANTS TO WITHDRAW
            if amount_to_withdraw > (acc_amount):
                messages.error(request, f"Insufficient Balance!. Your balance is insufficient to carry out this transaction.")
                return redirect("userdashboard:request_withdraw")
            
            tran_ref = generate_ref()

            # SAVING THE USER TRANSACTION
            user_tran = TransactionRecord(
                username=request.user, amount=amount_to_withdraw,
                transaction_type="WITHDRAWAL", transaction_referrence=tran_ref,
                date = datetime.now(), status="PENDING"
            )
            user_tran.save()

            if WithdrawalTransaction.objects.filter(user=request.user).exists():
                WithdrawalTransaction.objects.filter(user=request.user).update(
                    amount_to_withdraw=amount_to_withdraw,
                    transaction_referrence=tran_ref,
                    withdraw_from="ACCOUNT BALANCE",
                    status="PENDING"
                )
            else:
                user_withdrawal = WithdrawalTransaction(
                    user=request.user,
                    amount_to_withdraw=amount_to_withdraw,
                    withdrawal_date=datetime.now(),
                    transaction_referrence=tran_ref,
                    withdraw_from="ACCOUNT BALANCE",
                    status="PENDING"
                )
                user_withdrawal.save()
                
            admin_emails = add_admin_mail()
            wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
            send_mail(
                f"Withdrawal Request by {request.user}",
                f"Withdrawal request from your user. Username: {request.user}, Email: {request.user.email}, Cryptocurrency: {wallet_type} Wallet Address: {user_profile.wallet_address_used}, Amount ${amount_to_withdraw}"+
                " Please confirm this user in your dashboard before making any payment",
                settings.EMAIL_HOST_USER,
                admin_emails
            )
            return render(request, "account/withdraw-request-sent.html")
        template = "account/withdraw.html"
        registration_form = WalletSelectForm()
        return render(request, template, {"user_detail":user_profile, "transactions": user_deposit_tran, "form": registration_form})
    
    # WHEN DAYS IS LESS THAN 7, BUT USER HAS ACCUMULATED PERCENTAGE INTEREST
    elif days < 7 and aval_amount > 0 and user_deposit_tran.status == "APPROVED":
        if request.method == "POST":
            amount_to_withdraw = request.POST.get("amount", None).strip()
            wallet_type = request.POST.get("wallet_type", None)


            COINS = ["BITCOIN", "BITCOIN CASH", "ETHEREUM", "STELLAR", "LITECOIN"]
            if wallet_type not in COINS:
                messages.error(request, "Please select the wallet address for transaction")
                return redirect("userdashboard:request_withdraw")
            
            user_profile = get_object_or_404(UserProfile, user=request.user)
            
            # GETTING THE WALLET ADDRESS OF THER USER WHERE HE/SHE WANTS TO PAY
            if wallet_type == COINS[0]:
                # GETTING THE WALLET ADDRESS THE USER WANTS WANTS THE COIN TO BE SENT TO
                user_wallet_address = user_profile.bitcoin_address
            if wallet_type == COINS[1]:
                user_wallet_address = user_profile.bitcoin_cash_address
            if wallet_type == COINS[2]:
                user_wallet_address = user_profile.ethereum_address
            if wallet_type == COINS[3]:
                user_wallet_address = user_profile.stellar_address
            if wallet_type == COINS[4]:
                user_wallet_address = user_profile.litecoin_address

            # CHECKING IF THE WALLET ADDRESS IS NONE OR INVALID
            profile_id = UserProfile.objects.get(user=request.user).id
            if user_wallet_address is None:
                wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
                messages.error(request, f"Your {wallet_type} wallet address was not found. please update your wallet addresses for you to withdraw through it.")
                return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
            
            # CHECKING IF THE WALLET ADDRESS IS VALID
            if len(user_wallet_address) < 5:
                wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
                messages.error(request, f"Your {wallet_type} wallet address seems incomplete, valid wallet address ranges from 8 and above of character. Please update your wallet addresses")
                return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
                
            # SAVING THE LATEST WALLET ADDRESS USED FOR TRANSACTION
            user_profile.wallet_address_used = user_wallet_address
            user_profile.save()

            try:
                amount_to_withdraw = round(float(amount_to_withdraw), 2)
            except ValueError:
                messages.error(request, "Please enter amount as number")
                return redirect("userdashboard:request_withdraw")

            # CHECKING THE AMOUNT THE USER WANTS TO WITHDRAW
            if amount_to_withdraw > (aval_amount):
                messages.error(request, f"Insufficient Balance!. Your balance is insufficient to carry out this transaction. Your available balance is ${round(aval_amount, 2)}")
                return redirect("userdashboard:request_withdraw")
            
            tran_ref = generate_ref()

            # SAVING THE USER TRANSACTION
            user_tran = TransactionRecord(
                username=request.user, amount=amount_to_withdraw,
                transaction_type="WITHDRAWAL", transaction_referrence=tran_ref,
                date = datetime.now(), status="PENDING"
            )
            user_tran.save()

            if WithdrawalTransaction.objects.filter(user=request.user).exists():
                WithdrawalTransaction.objects.filter(user=request.user).update(
                    amount_to_withdraw=amount_to_withdraw,
                    transaction_referrence=tran_ref,
                    withdraw_from="ACCOUNT BALANCE",
                    status="PENDING"
                )
            else:
                user_withdrawal = WithdrawalTransaction(
                    user=request.user,
                    amount_to_withdraw=amount_to_withdraw,
                    withdrawal_date=datetime.now(),
                    transaction_referrence=tran_ref,
                    withdraw_from="ACCOUNT BALANCE",
                    status="PENDING"
                )
                user_withdrawal.save()
                
            admin_emails = add_admin_mail()
            wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
            send_mail(
                f"Withdrawal Request by {request.user}",
                f"Withdrawal request from your user. Username: {request.user}, Email: {request.user.email}, Cryptocurrency: {wallet_type} Wallet Address: {user_profile.wallet_address_used}, Amount ${amount_to_withdraw}"+
                " Please confirm this user in your dashboard before making any payment",
                settings.EMAIL_HOST_USER,
                admin_emails
            )

            # SENDING EMAIL TO USER WHEN BALANCE IS REINVESTED
            send_mail(
            f"Withdrawal Requested",
            f"Hey {request.user}!! You have request for withdrawal; Amount: ${amount_to_withdraw}, Wallet Address: {user_profile.wallet_address_used}, Cryptocurrency: {wallet_type}" +
            " If you are not aware of the action, contact the admin now",
            settings.EMAIL_HOST_USER,
            [request.user.email]
            )
            return render(request, "account/withdraw-request-sent.html")
        template = "account/withdraw.html"
        registration_form = WalletSelectForm()
        return render(request, template, {"user_detail":user_profile, "transactions": user_deposit_tran, "form": registration_form})
        
    else:
        err_text = """
        <p style="color: red;">OOPS!! Sorry you can't withdraw now.<br>
        REASONS:<br>1. Your Balance is not due for withdrawal.<br>2.Deposit has not reached seven (7) days of accumulation
        <br>3. You requested for a deposit which has not been approved.<br>Do chat the admin for assistance 
        </p>
        """
        return HttpResponse(err_text)


@login_required(login_url="userdashboard:login")
def withdraw_bonus(request):
    """HANDLES USER BONUS WITHDRAWAL"""
    template = "account/withdraw_bonus.html"

    if request.method == "POST":
        amount = request.POST.get("amount", None)
        wallet_type = request.POST.get("wallet_type", None)
        
        COINS = ["BITCOIN", "BITCOIN CASH", "ETHEREUM", "STELLAR", "LITECOIN"] 
        if wallet_type not in COINS:
            messages.error(request, "Please select the wallet address for transaction")
            return redirect("userdashboard:request_withdraw")
        
        user_profile = get_object_or_404(UserProfile, user=request.user)
        
        # GETTING THE WALLET ADDRESS OF THER USER WHERE HE/SHE WANTS TO PAY
        if wallet_type == COINS[0]:
            # GETTING THE WALLET ADDRESS THE USER WANTS WANTS THE COIN TO BE SENT TO
            user_wallet_address = user_profile.bitcoin_address
        if wallet_type == COINS[1]:
            user_wallet_address = user_profile.bitcoin_cash_address
        if wallet_type == COINS[2]:
            user_wallet_address = user_profile.ethereum_address
        if wallet_type == COINS[3]:
            user_wallet_address = user_profile.stellar_address
        if wallet_type == COINS[4]:
            user_wallet_address = user_profile.litecoin_address

        # CHECKING IF THE WALLET ADDRESS IS NONE OR INVALID
        profile_id = UserProfile.objects.get(user=request.user).id
        if user_wallet_address is None:
            wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
            messages.error(request, f"Your {wallet_type} wallet address was not found. please update your wallet addresses for you to withdraw through it.")
            return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
        
        # CHECKING IF THE WALLET ADDRESS IS VALID
        if len(user_wallet_address) < 5:
            wallet_type = wallet_type.replace("_address", "").upper().replace("_", " ")
            messages.error(request, f"Your {wallet_type} wallet address seems incomplete, valid wallet address ranges from 8 and above of character. Please update your wallet addresses")
            return redirect(f"/account/user/update-wallet-addresses/{profile_id}/")
            
        # SAVING THE LATEST WALLET ADDRESS USED FOR TRANSACTION
        user_profile.wallet_address_used = user_wallet_address
        user_profile.save()


        try:
            amount = round(float(amount), 2)
        except ValueError:
            messages.error(request, "Please enter a valid amount")
            return redirect(".")
        if ReferralBonus.objects.filter(username=request.user).exists():
            user_bonus = ReferralBonus.objects.get(username=request.user)
            if amount > user_bonus.accumulated_bonus:
                messages.error(request, "Your bonus balance is insufficient for the amount you want to withdraw!")
                return redirect(".")
            # SEND BONUS WITHDRAWAL EMAIL TO ADMIN AND RETURN
            tran_ref = generate_ref()

             # SAVING THE USER TRANSACTION
            user_tran = TransactionRecord(
                username=request.user, amount=amount,
                transaction_type="BONUS WITHDRAWAL", transaction_referrence=tran_ref,
                date = datetime.now(), status="PENDING"
            )
            user_tran.save()

            if WithdrawalTransaction.objects.filter(user=request.user).exists():
                    WithdrawalTransaction.objects.filter(user=request.user).update(
                    amount_to_withdraw=amount,
                    transaction_referrence=tran_ref,
                    withdraw_from="REFERRAL BONUS",
                    status="PENDING",
                )
            else:
                user_withdrawal = WithdrawalTransaction(
                    user=request.user,
                    amount_to_withdraw=amount,
                    withdrawal_date=datetime.now(),
                    transaction_referrence=tran_ref,
                    withdraw_from="REFERRAL BONUS",
                    status="PENDING"
                )
                user_withdrawal.save()
            admin_emails = add_admin_mail()
            user_profile = get_object_or_404(UserProfile, user=request.user)
            send_mail(
                "Bonus Withdrawal Request",
                f"{request.user} requesting to withdrawal bonus accumulated. Username: {request.user}, Email: {request.user.email}, CRYPTOCURRENCY: {wallet_type}, Wallet Address: {user_profile.wallet_address_used}, Amount: ${amount}. Do confirm this user before approving payment.",
                settings.EMAIL_HOST_USER,
                admin_emails
            )
            messages.info(request, "Your request has been accepted and it's being processed. Your bonus will be paid int to your provided wallet address!!")
            return redirect("userdashboard:account_details")
        else:
            messages.error(request, "You don't seem to have a bonus accumulated. Please contact admin for help")
            return redirect(".")

    user_profile = UserProfile.objects.get(user=request.user)
    registration_form = WalletSelectForm()
    return render(request, template, {"wallet_addr": user_profile.wallet_address_used, "form": registration_form})


class UpdateWalletView(UpdateView):
    template_name = "account/update_wallet.html"
    success_url = reverse_lazy("userdashboard:user_profile")
    model = UserProfile
    fields = (
        "bitcoin_address", "bitcoin_cash_address",
        "ethereum_address", "stellar_address",
        "litecoin_address",
        )
    

def handl_user_mail_admin(request):
    """HANDELS USER SENDING EMAIL TO THE ADMIN"""
    if request.method == "POST":
        username = request.POST.get("username", None)
        email = request.POST.get("email", None)
        subject = request.POST.get("subject", None)
        message = request.POST.get("message", None)

        if username and email and subject and message:

            admin_emails = add_admin_mail()
            # SEND EMAIL TO ADMIN
            send_mail(
            str(subject),
            f"Message from your user, Username: {username} Email: {email} Message: {message}",
            settings.EMAIL_HOST_USER,
            admin_emails
            )
            messages.info(request, "Admin has received your mail. Expect replies soonest!")
            return redirect("userdashboard:user_profile")
        else:
            messages.error(request, "Please fill-out all field!!")
            return redirect("userdashboard:user_profile")
    return render(request, "account/email-admin.html")
