# accounts, managers.py:
from django.contrib.auth.base_user import BaseUserManager

# usage: objects = CustomUserManager() in models.py
class CustomUserManager(BaseUserManager):
    """
    # as github code:
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)
    """
    # this func omitted by by yasir bro in class
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)        
        user = self.model(email=email, **extra_fields)  # user = CustomUser(email=email)     
        user.set_password(password)
        user.save() # user.save(using=self._db)        
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        # user.is_staff = True
        extra_fields.setdefault("is_superuser", True)
        # user.is_superuser = True
        # extra_fields.setdefault("is_verified", True)
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # saves as hash
        # user.is_verified = True        
        user.save()
        return user

	

