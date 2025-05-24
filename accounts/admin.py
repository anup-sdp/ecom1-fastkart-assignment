# accounts, admin.py:
from django.contrib import admin

from .models import CustomUser

#admin.site.register(CustomUser)

"""	"""
# raise AlreadyRegistered(msg): django.contrib.admin.exceptions.AlreadyRegistered: The model CustomUser is already registered in app 'accounts'. # ok after disabling admin.site.register(CustomUser)
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change): # overrides save_model from ModelAdmin
        if form.cleaned_data.get("password"):
            obj.set_password(form.cleaned_data["password"])
        return super().save_model(request, obj, form, change)

# ^ this used because previously after changing pw for admin in adminpanel, they were being saved without hashing.