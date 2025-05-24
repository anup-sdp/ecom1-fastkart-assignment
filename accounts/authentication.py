# accounts, authentication.py:

"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        OurUser = get_user_model()
        try:
            user = OurUser.objects.get(email=email)
            if user.check_password(password):
                return user
        except OurUser.DoesNotExist:
            return
"""

"""
to fix in sttings.py:
AUTHENTICATION_BACKENDS = [
    "accounts.authentication.EmailBackend",
    #"django.contrib.auth.backends.ModelBackend",  # with multiple backends, problem while resetting password. but without it cant login to admin panel. #edited authentication.py
]
in email confirmation button click error:
ValueError at /accounts/reset-password-confirm/MTY/cq0mrb-fb4da54b42c132bc952f2066ee94f619/
You have multiple authentication backends configured and therefore must provide the `backend` argument or set the `backend` attribute on the user.
"""

# accounts/authentication.py

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        # Treat Django admin’s `username` as email
        email = username or kwargs.get(UserModel.USERNAME_FIELD)
        if not email or not password:
            return None

        try:
            user = UserModel.objects.get(**{UserModel.USERNAME_FIELD: email})
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
