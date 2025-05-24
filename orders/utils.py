from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def send_order_confirmation_email(user, order):
    if not user.is_authenticated:
        return
    email_subject = "Thanks For your Order"
    context = {"user": user, "order": order}
    email_body = render_to_string("orders/order-success.html", context)

    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],  # email for non uers ? --------------
    )

    email.content_subtype = "html"
    email.send()

