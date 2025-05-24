from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse

def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    print("in send_verification_email(), token = ", token)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    print("in send_verification_email(), user.pk = ", user.pk)  # user.pk =  24
    print("in send_verification_email(), uid, type = ", uid, type(uid))  # MjQ <class 'str'>

    current_site = get_current_site(request)
       
    verification_link = f"http://{current_site.domain}/accounts/verify/{uid}/{token}"
    # TODO: use reverse() 
    # Django’s reverse() function generates a URL from your named URL pattern, so you never have to hardcode URL paths.
    # verification_link = request.build_absolute_uri(reverse("verify-email", kwargs={"uidb64": uid, "token": token}))
    email_subject = "Verify Your Email Address"
    #email_body = f"Verification link: {verification_link}"
    
    email_body = render_to_string(
        "accounts/verification_email.html",
        {"user": user, "verification_link": verification_link},  # email: Hi None And Welcome To Fastkart.! -- fixed
    )

    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL, # or settings.EMAIL_HOST_USER 
        to=[user.email],
    )

    email.content_subtype = "html"
    email.send()


def send_password_reset_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    current_site = get_current_site(request)
    # TODO: use reverse()
    verification_link = (
        f"http://{current_site.domain}/accounts/reset-password-confirm/{uid}/{token}"
    )

    email_subject = "Reset Your Password"
    email_body = render_to_string(
        "accounts/verification_email.html",  # or areate a new reset_password.html ?
        {"user": user, "verification_link": verification_link},
    )

    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.content_subtype = "html"
    email.send()