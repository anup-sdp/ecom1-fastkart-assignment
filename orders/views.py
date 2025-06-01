#import datetime
from datetime import datetime
import random
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from sslcommerz_python_api import SSLCSession

from carts.models import Cart, CartProduct
from carts.utils import get_session_key
from products.models import Product

from .models import Order, OrderProduct, Payment
from .utils import send_order_confirmation_email


from django.contrib import messages
from django.db import transaction # ---

@csrf_exempt
@login_required
def place_order(request):    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).last()
    else:  
        cart = Cart.objects.filter(session_key=get_session_key).last()
    
    cart_products = CartProduct.objects.filter(cart=cart).select_related("product") 
    if cart_products.count() == 0:
        messages.info(request, f"Your Cart is Empty")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))
    
    total_price = 0
    quantity = 0
    for item in cart_products:
        total_price += item.product.price* (100-item.product.discount_percentage)/100 * item.quantity
        quantity += item.quantity

    if request.method == "POST":
        payment_option = request.POST.get("payment_method")

        try:
            # Use database transaction to ensure data consistency
            with transaction.atomic():
                order_number = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"
                current_user = request.user

                order = Order.objects.create(
                    user=current_user,
                    mobile=current_user.mobile,
                    address_line_1=current_user.address_line_1,
                    address_line_2=current_user.address_line_2,
                    country=current_user.country,
                    postcode=current_user.postcode,
                    city=current_user.city,
                    order_note=request.POST.get("order_note", ""),
                    order_total=total_price,
                    status="Pending",
                    order_number=order_number,
                )

                # Create order products and check stock availability
                for cart_item in cart_products:
                    # Check if enough stock is available
                    product = Product.objects.select_for_update().get(id=cart_item.product.id)
                    if product.stock < cart_item.quantity:
                        raise ValueError(f"Insufficient stock for {product.name}. Available: {product.stock}, Requested: {cart_item.quantity}")

                    OrderProduct.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        product_price=cart_item.product.price *(100-cart_item.product.discount_percentage)/100,  # discount_percentage
                    )

                if current_user.is_authenticated:
                    send_order_confirmation_email(current_user, order)
                    messages.info(request, "An email was sent!")

                if payment_option == "cash":  # todo: create and save payment object for cash on delevery
                    # Reduce product stock for cash payments (immediate confirmation)
                    reduce_product_stock(cart_products)
                    # Delete cart products after successful stock reduction
                    cart_products.delete()
                    return HttpResponse("<h3>Your payment with cash is successful</h3>")
                elif payment_option == "sslcommerz":
                    # For SSLCommerz, stock will be reduced after payment confirmation
                    return redirect("payment")

        except ValueError as ve:
            messages.error(request, str(ve))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))
        except Exception as e:
            messages.error(request, f"Error occurred: {str(e)}")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))

    context = {
        "total_price": total_price,
        "quantity": quantity,
        "cart_items": cart_products,
        "cart_count": quantity,        
        "grand_total": total_price + getattr(settings, 'DELIVERY_CHARGE', 0),
    }    
    return render(request, "orders/checkout.html", context)


#@login_required
def payment(request):  # non-cash payment, when payment_option == "sslcommerz"
    # https://pypi.org/project/sslcommerz-python-api/
    # https://pypi.org/project/sslcommerz-python/
    # https://www.youtube.com/watch?v=krTt8Xdchow&list=PLJh8Hi_cW8DZzzjC0tBLqhgPTv2NBlnCc&index=81&t=20s
    mypayment = SSLCSession(
        sslc_is_sandbox=settings.SSLCOMMERZ_IS_SANDBOX,
        sslc_store_id=settings.SSLCOMMERZ_STORE_ID,
        sslc_store_pass=settings.SSLCOMMERZ_STORE_PASS,
    )

    status_url = request.build_absolute_uri("payment_status")  # was "payment_status" or "sslc/status" ? ------------

    mypayment.set_urls(
        success_url=status_url,
        fail_url=status_url,
        cancel_url=status_url,
        ipn_url=status_url,
    )

    user = request.user
    order = Order.objects.filter(user=user, status="Pending").last()  # ---------- get order using session id for non users. ------------

    mypayment.set_product_integration(
        total_amount=order.order_total,  # Decimal(order.order_total),
        currency="BDT",
        product_category="clothing",
        product_name="demo-product", # in sslc only 1 product can be given at a time
        num_of_item=2,
        shipping_method="YES",
        product_profile="None",
    )

    # mypayment.set_customer_info(
    #     name=user.username,
    #     email=user.email,
    #     address1=order.address_line_1,
    #     address2=order.address_line_1,
    #     city=order.city,
    #     postcode=order.postcode,
    #     country=order.country,
    #     phone=order.mobile,
    # )

    # mypayment.set_shipping_info(
    #     shipping_to=user.first_name,  # user.get_full_name(),  # -----
    #     address=order.full_address(),
    #     city=order.city,
    #     postcode=order.postcode,
    #     country=order.country,        
    # )
    mypayment.set_customer_info(
        name='John Doe',
        email='johndoe@email.com',
        address1='demo address',
        address2='demo address 2',
        city='Dhaka', postcode='1207',
        country='Bangladesh',
        phone='01711111111'
    )

    mypayment.set_shipping_info(
        shipping_to='demo customer',
        address='demo address',
        city='Dhaka',
        postcode='1209',
        country='Bangladesh'
    )

    response_data = mypayment.init_payment()  # The code works synchronously (not async), and the network delay is handled transparently by the library’s blocking HTTP call.  
    # if needed we can use Django’s async views
    print(response_data)    
    if response_data['status'] == 'SUCCESS':
        print(response_data['status'])
        print(response_data['sessionkey'])
        print(response_data['GatewayPageURL'])   
    
    if response_data["status"] == "FAILED":
        print('failedreason: ',response_data['failedreason'])
        order.status = "failed"        
        order.save()                
        messages.info(request, f"Payment failed! error: {response_data['failedreason']}")  # occured: Payment failed! error: Store Credential Error Or Store is De-active
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect(response_data["GatewayPageURL"]) # go to sslcs url, from there will be back to status_url


@csrf_exempt
def payment_status(request):  # in yasir bros code payment_status + sslc_complete same function
    if request.method == "POST":  # sslc_status
        payment_data = request.POST
        if payment_data["status"] == "VALID":
            val_id = payment_data["val_id"]
            tran_id = payment_data["tran_id"]            
            messages.success(request, "Your payment was successful!")
            return HttpResponseRedirect(reverse("sslc_complete", kwargs={"val_id": val_id, "tran_id": tran_id}))  # search: HttpResponseRedirect, reverse --------
        else:
            #order = Order.objects.filter(user=request.user).last()
            #order.status = 'failed'
            # restock product
            #order.save()
            # return JsonResponse({"status": "error", "message": "Payment failed"})  # or show a error page
            return render(request,"orders/payment-failed.html")  # extend base-global for this file --------------------------------- TODO
    
    return HttpResponse("<h3>GET request, in payment_status() in orders </h3>")  #return render(request, "orders/status.html") # if not POST --- when ?


def sslc_complete(request, val_id, tran_id):
    try:
        with transaction.atomic():
            order = Order.objects.filter(user=request.user, status="Pending").last()
            if not order:
                return HttpResponse("No pending order found", status=404)

            # Get the order products to reduce stock
            order_products = OrderProduct.objects.filter(order=order).select_related("product")
            
            # Check stock availability before reducing
            for order_product in order_products:
                product = Product.objects.select_for_update().get(id=order_product.product.id)
                if product.stock < order_product.quantity:
                    # Log this issue or handle it appropriately
                    messages.warning(request, f"Warning: Insufficient stock for {product.name}")
                    # You might want to partially fulfill or cancel the order here
                    
            payment = Payment.objects.create(
                user=request.user,
                payment_id=val_id,
                payment_method="SSLCommerz",
                amount_paid=order.order_total,
                status="Completed",
            )
           
            order.status = "Completed"
            order.payment = payment
            order.save()
            
            # Reduce product stock after successful payment
            reduce_product_stock_from_order(order_products)
            
            # Delete user's cart after successful payment and stock reduction
            Cart.objects.filter(user=request.user).delete()

        context = {
            "order": order,
            "transaction_id": tran_id,
        }
        return render(request, "orders/status.html", context)

    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500)


# Helper function to reduce stock from cart products
def reduce_product_stock(cart_products):
    """
    Reduce product stock based on cart products.
    Used for immediate payments like cash.
    """
    for cart_item in cart_products:
        product = Product.objects.select_for_update().get(id=cart_item.product.id)
        if product.stock >= cart_item.quantity:
            product.stock -= cart_item.quantity
            # Set availability to False if stock reaches 0
            if product.stock == 0:
                product.available = False
            product.save()
        else:
            # This shouldn't happen if we checked earlier, but just in case
            raise ValueError(f"Insufficient stock for {product.name}")


# Helper function to reduce stock from order products  
def reduce_product_stock_from_order(order_products):
    """
    Reduce product stock based on order products.
    Used after payment confirmation (like SSLCommerz).
    """
    for order_product in order_products:
        product = Product.objects.select_for_update().get(id=order_product.product.id)
        if product.stock >= order_product.quantity:
            product.stock -= order_product.quantity
            # Set availability to False if stock reaches 0
            if product.stock == 0:
                #product.available = False
                pass
            product.save()
        else:
            # Log this issue - payment was successful but stock is insufficient
            # You might want to implement a notification system here
            print(f"Warning: Insufficient stock for {product.name} in order {order_product.order.order_number}")


# Optional: Function to handle failed payments and restore stock
def restore_product_stock_for_failed_order(order):
    """
    Restore product stock if payment fails.
    This can be called from a payment failure handler.
    """
    order_products = OrderProduct.objects.filter(order=order).select_related("product")
    
    with transaction.atomic():
        for order_product in order_products:
            product = Product.objects.select_for_update().get(id=order_product.product.id)
            product.stock += order_product.quantity
            if product.stock > 0:
                product.available = True
            product.save()
        
        # Update order status
        order.status = "Cancelled"
        order.save()