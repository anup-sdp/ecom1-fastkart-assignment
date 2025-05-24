# accounts, models.py:
from django.db import models
from django.contrib.auth.models import AbstractUser
from accounts.managers import CustomUserManager
#from django.contrib.auth.models import User # default user

class CustomUser(AbstractUser):  # email, password for login will be used in this project, try google/phone number login latter
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    address_line_1 = models.CharField(null=True, blank=True, max_length=100)
    address_line_2 = models.CharField(null=True, blank=True, max_length=100) #  to distinguish between "no data" (NULL) and "empty string"
    # null=True, Database-level: This allows the field to be stored as NULL in the database when there's no value.
    # blank=True, Validation-level: This allows the field to be empty in forms (including Django admin).
    city = models.CharField(blank=True, max_length=20)
    postcode = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20) #  let empty strings be stored instead of NULL
    mobile = models.CharField(null=True, blank=True, max_length=15) # mobile = None vs mobile = ""

    profile_picture = models.ImageField(upload_to="user_profile", blank=True, null=True)
    
    username = None
    objects = CustomUserManager() # use it instead of UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []    
    
    
    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"

# how to create superuser after this ?
"""
for,
createsuperuser problem: not being able to create as no username:
in class AbstractUser(inheritted by our CustomUser) there is, objects = UserManager(), it defines create_superuser(),
so instead use CustomUserManager. (did not override it)
"""	