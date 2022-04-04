from django.urls import path         

from .views import (
    home_view,  about_view,
    terms_condition_view, # faq_view,
    investment_plans_view, handle_referral_link,
    contact_us, services_view,
    )

app_name  = "apexapp"
urlpatterns = [
    path("", home_view, name="home"),
    path("referral-link<int:id>/referrer=<str:username>/", handle_referral_link, name="referral_link"),
    path("about-us/", about_view, name="about_us"),
    path("terms-and-conditions/", terms_condition_view, name="policies"),
    # path("frequently-asked-questions/", faq_view, name="faq"),
    path("investment-plans/", investment_plans_view, name="investment_plans_view"),
    path("contact-us/", contact_us, name="contact_us"),
    path("our-services/", services_view, name="services"),
]
