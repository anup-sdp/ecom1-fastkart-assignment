# accounts, views.py
from django.shortcuts import render

# Create your views here.

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from accounts.forms import CustomUserRegistrationForm
from accounts.models import CustomUser
from accounts.utils import send_verification_email, send_password_reset_email
from orders.models import Order, OrderProduct  

"""
def landing(request):
    #return render(request, "accounts/temp.html")
    context = {}
    if request.user.is_authenticated:
        context['username'] = request.user.first_name + " " + request.user.last_name 
    return render(request, "landing-page.html", context) # in project level templates folder.
"""

def privacy_policy(request):
    return render(request, "privacy_policy.html") # in project level templates folder.


def terms_and_conditions(request):
    return render(request, "terms_and_conditions.html") # in project level templates folder.


# register
def user_signup(request):
    if request.method == "POST":
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            #user = form.save(commit=False)
            user = form.save() # because user.pk =  None in send_verification_email()
            #print("got user in user_signup()")  # printed
            send_verification_email(request, user) # in utils.py, # TO DO: limit verification time
            #user.save()
            messages.info(request, "We have sent you an verfication email")
            return redirect("login")
        # TO DO: show form errors in template
        # form is invalid: push each error into messages, then re-render with form
        # Handle form errors
        for field, errors in form.errors.items(): # form.errors is a dict: field name → list of errors            
            for error in errors:                
                messages.info(request, f"{error}") # messages.error(request, f"{field}: {error}")
        # Handle non-field errors
        for error in form.non_field_errors():
            messages.error(request, error)
        # now render the template, passing the bound form back
        return render(request, "accounts/signup.html", {"form": form})    
    # GET:
    return render(request, "accounts/signup.html")
    # return render(request, "accounts/signup.html", {"form": CustomUserRegistrationForm()})



def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password) # authenticate() in ModelBackend (from django.contrib.auth.backends import ModelBackend)
        # as we are using email instead of username here, authenticate() is modified in EmailBackend class in authentication.py
        # mentioned in settings.py in AUTHENTICATION_BACKENDS, / !login worked without it.
        if not user: # user is None
            messages.error(request, "Invalid username or password.")
        elif not user.is_verified:
            messages.error(request, "Your email is not verified yet.")
        else:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect("profile")
            #return render(request, "custom-try.html") # ok

    # TODO: use a form and show form errors in template
    return render(request, "accounts/login.html")


@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def user_dashboard(request):
    user = request.user
    
    if request.method == "POST": 
        # Profile update logic (unchanged)
        for field in ("email","mobile","address_line_1","address_line_2","city","postcode","country"):
            val = request.POST.get(field, "").strip()
            if val:
                setattr(user, field, val)
        user.save()
        messages.info(request, 'Profile updated successfully!')
        return redirect("profile")
    
    # Fetch user's past orders with related data
    past_orders = Order.objects.filter(
        user=user,
        status__in=["Completed", "Delivered"]  # Only completed orders
    ).prefetch_related(
        'order_products__product'  # Prefetch to avoid N+1 queries
    ).order_by('-created_at')  # Most recent first
    
    # Get all order products from completed orders
    order_products = OrderProduct.objects.filter(
        order__user=user,
        order__status__in=["Completed", "Delivered"]
    ).select_related(
        'product', 'order'
    ).order_by('-created_at')  # Most recent first
    
    # Calculate total orders and total spent
    total_orders = past_orders.count()
    total_spent = sum(order.order_total for order in past_orders)
    
    context = {
        "user_info": user,
        "past_orders": past_orders,
        "order_products": order_products,
        "total_orders": total_orders,
        "total_spent": total_spent,
    }
    return render(request, "accounts/profile.html", context)


def verify_email(request, uidb64, token):
    try:
        print("in verify_email(), uidb64 = ", uidb64)  # uidb64 =  MjQ
        uid = urlsafe_base64_decode(uidb64).decode()
        print("in verify_email(), uid, type = ", uid, type(uid))  # 24 <class 'str'>
        #user = CustomUser.objects.get(pk=uid)       
        user = CustomUser.objects.get(pk=int(uid))  # Convert to int
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist) as e:
        print(f"Error occurred: {str(e)}")
        messages.info(request, f"Error: {str(e)}")
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.info(request, "Your email has been verified successfully.")
        return redirect("login")
    else:
        messages.info(request, "The verification link is invalid or has expired.")
        return redirect("signup")


def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.info(request, "User does not exist.") # messages.error
            return redirect("password-reset")

        send_password_reset_email(request, user) # in utils.py
        messages.info(request, "We have sent you an email with password reset instructions")        
        return redirect("login")

    return render(request, "accounts/forgot_password.html")


def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        login(request, user)
        return redirect("new-password")
    else:
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect("login")


@login_required
def set_new_password(request):
    if request.method == "POST":
        # TO DO: use form, and add 'Confirm Password'
        password = request.POST.get("password")
        user = request.user
        user.set_password(password)
        user.save()
        messages.success(request, "Password updated successfully.")
        return redirect("profile")
    return render(request, "accounts/new-password.html")