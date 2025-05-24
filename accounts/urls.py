# accounts, urls.py
# press ctrl + i for copilot
from django.urls import path

from . import views

urlpatterns = [
	#path("landing/", views.landing, name="landing"), # http://127.0.0.1:8000/accounts/landing
    path("signup/", views.user_signup, name="signup"),  # http://127.0.0.1:8000/accounts/signup
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.user_dashboard, name="profile"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify-email"),
    path("reset-password/", views.reset_password, name="password-reset"),
    path("reset-password-confirm/<uidb64>/<token>/", views.reset_password_confirm, name="reset_password_confirm"),
    path("set-new-password/", views.set_new_password, name="new-password"),
]