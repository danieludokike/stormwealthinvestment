import re
from django.contrib.auth.models import User
from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives, EmailMessage

from django.template.loader import render_to_string
from django.utils.html import strip_tags

REGISTRATION_SUCCESS_TEMPLATE_EMAIL, INVOICE_TEMPLATE = "account/registration_email.html", "account/invoice.html"


admin_mail = []


def add_admin_mail():
    """"ADDS ALL THE ADMIN EMAIL"""
    admin = User.objects.filter(is_superuser=True)

    for user in admin:
        admin_mail.append(user.email)
    return admin_mail


def is_empty(*args):
    """CHECKS IF THE PASSED VAR IS EMPTY"""
    for var in args:
        if var == "" or var is None:
            return True
    return False


def is_equal(val1, val2):
    """CHECKS IF THE TWO PASSED VALUES ARE EQUAL"""
    if val1 == val2:
        return True
    return False


def is_email_valid(email_address):
    """CHECKS IF AN EMAIL ADDRESS IS VALID"""
    if not re.search(r"^\w+@\w+\.\w+$", email_address):
        return False
    return True


def is_email_taken(email_address):
    """CHECKS IF THE GIVEN EMAIL ADDRESS EXISTS IN THE DATABASE"""
    if User.objects.filter(email=email_address).exists():
        return True
    return False


def is_username_valid(username):
    """CHECKS IF THE GIVEN USERNAME IS EXISTS IN THE DATABASE"""
    if not re.search(r"^\w+$", username):
        return False
    return True


def is_username_taken(username):
    """CHECKS IF THE GIVEN USERNAME IS EXISTS IN THE DATABASE"""
    if User.objects.filter(username=username).exists():
        return True
    return False


def is_safe(password):
    """CHECKS IF THE PASSWORD LENGTH IS MINIMUM OF EIGHT"""
    if len(password) < 8 or not password.isalnum():
        return False
    return True


def validate_wallet_addr(w_addr):
    """CHECKS IF THE WALLET ADDRESS HAS MINIMUM DIGITS"""
    if len(w_addr) < 5:
        return False
    return True


def redirect_to_singup_page(request, template_name, form_class):
    """RENDERS THE REGISTRATION PAGE"""
    return render(request, template_name, {"form": form_class})


def email_user_registration(username, password, to_email):
    """SENDS EMAIL TO THE USER"""
    context = {
        "title": username,
        "username": username,
        "password":password,
        "content": "Your account registration was successful. Do fund your wallet and start earning",
    }
    html_content = render_to_string(REGISTRATION_SUCCESS_TEMPLATE_EMAIL, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(    
        "Account Registered Successfully",
        text_content,
        settings.EMAIL_HOST_USER,
        [to_email,]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    return


def email_referrer(to_email, referree, total_ref):
    """SENDS EMAIL TO THE REFERRER"""
    send_mail(
        "User Registered With Your Referral Link",
        f"{referree} has registered with your referral link. You now have {total_ref} person(s) registered with your link. Keep " +
        "sending your link and get bonus once your referree makes a deposit",
        settings.EMAIL_HOST_USER,
        [to_email,]
    )
    return


def email_admin(username, amount, p_type, earning_rate):
    """Sends email to the admin"""
    admin_emails = add_admin_mail()
    send_mail(
        "Payment Process Iniated",
        f"User, {username} has iniated payment process: Amount: ${amount}, Plan Type: {p_type}, Earning Rate: {earning_rate}." +
        "Do confirm this payment before approving the transaction",
        settings.EMAIL_HOST_USER,
        admin_emails
    )


def  email_user_deposit(username, tran_ref, amount, date, wallet_addr, to_email, status):
    """SEND EMAIL TO USER AFTER DEPOSIT"""
    context = {
        "title": username,
        "user": username,
        "tran_ref":tran_ref,
        "amount": amount,
        "date": date,
        "wallet_addr": wallet_addr,
        "status": status,
        "tran_type": "Deposit approved",
    }
    html_content = render_to_string(INVOICE_TEMPLATE, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(    
        f"{username}'s Deposit Invoice",
        text_content,
        settings.EMAIL_HOST_USER,
        [to_email,]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    return


def  email_user_withdrawal(username, tran_ref, amount, date, wallet_addr, to_email, status, w_type):
    """SEND EMAIL TO USER AFTER WITHDRAWAL"""
    context = {
        "title": username,
        "user": username,
        "tran_ref":tran_ref,
        "amount": amount,
        "date": date,
        "wallet_addr": wallet_addr,
        "status": status,
        "tran_type": "Withdrawal Invoice. Sent to your provided wallet address",
    }
    
    if w_type == "ACC":
        context["type"] = "Withdrawal From Account Balance"
    else:
        context["type"] = "Withdrawal From Referral Bonus"

    html_content = render_to_string(INVOICE_TEMPLATE, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(    
        f"Invoice for {username}",
        text_content,
        settings.EMAIL_HOST_USER,
        [to_email,]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    return