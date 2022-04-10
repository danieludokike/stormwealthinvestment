from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages


from .models import CompanyYoutubeTubeVideo, Top10Deposit, Top10Withdrawal

def home_view(request):
    """RENDERS THE HOME PAGE ON REQUEST"""
    template = "infinityapp/index.html"
    video = CompanyYoutubeTubeVideo.objects.all().order_by("-id").first()
    top_deposit = Top10Deposit.objects.all().order_by("-id")[:10]
    top_withdraw = Top10Withdrawal.objects.all().order_by("-id")[:10]

    target = ["/","/about-us/", "/terms-and-conditions/", "/investment-plans/", "/frequently-asked-questions/", "/investment-plans/", "/contact-us/", "/our-services/", ]
    context = {
        "video": video,
        "top_deposit": top_deposit,
        "top_withdraw": top_withdraw,
        "target": target,
        "referrer": request.session.get('referrer', None),
    }
    return render(request, template, context)


def handle_referral_link(request, id, username):
    """HANDLES REFERRAL LINK"""
    if User.objects.filter(id=id).exists():
        username = User.objects.get(id=id).username
        print(username)
        request.session["referrer"] = username
        return redirect("apexapp:home")
    # SENDING ERROR OF THE REFERRAL LINK
    return HttpResponse(f"<p style='color:red;'>Invalid referral link! '{id}' is not recognized.<br> NOTE: referral links are case sensitive</p>")

def about_view(request):
    template = "infinityapp/about.html"
    print(request.path)
    # video = CompanyYoutubeTubeVideo.objects.all().order_by("-id").first()
    return render(request, template)


def terms_condition_view(request):
    template = "infinityapp/terms_and_condition.html"
    return render(request, template)


# def faq_view(request):
#     template = "apexapp/pages/faq.html"
#     return render(request, template)


def investment_plans_view(request):
    """Renders the investment plans on request"""
    template = "infinityapp/investment_plans.html"
    return render(request, template)


def contact_us(request):
    """JUST THANKS THE USER AFTER FORM SUBMIT"""
    if request.method == "POST":
        messages.info(request, "Thanks for your message. We are connecting to reply you as soon as possible")
        return redirect("apexapp:home")
    return render(request, "infinityapp/contact.html")



def services_view(request):
    """RENDERS THE SERVICES PAGE ON REQUEST"""
    return render(request, "infinityapp/services.html")
