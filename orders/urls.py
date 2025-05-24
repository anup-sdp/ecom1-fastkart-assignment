from django.urls import path

from . import views

urlpatterns = [
    path("", views.place_order, name="place_order"),
    path("payment/", views.payment, name="payment"),
    path("payment/payment_status", views.payment_status, name="payment_status"),  # payment_status vs was status (1st item)
    path("payments/sslc/complete/<val_id>/<tran_id>/", views.sslc_complete, name="sslc_complete",),
]
