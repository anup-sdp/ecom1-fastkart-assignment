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

@csrf_exempt
@login_required
def place_order(request):    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).last()
    else:  
        cart = Cart.objects.filter(session_key= get_session_key).last()
    cart_products = CartProduct.objects.filter(cart=cart).select_related("product") 
    if cart_products.count() == 0:
        messages.info(request, f"Your Cart is Empty")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))        
    
    total_price = 0
    quantity = 0
    for item in cart_products:
        total_price += item.product.price * item.quantity  # discount_percentage ? # in case of n+1 problem, for each item there will be a query.
        quantity += item.quantity

	#
    if request.method == "POST":   # clicked "place order" button
        payment_option = request.POST.get("payment_method")  # cash / sslcommerz

        try:            
            order_number = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"   # '20250514153045' (May 2025, 3:30:45 PM) + 6 digit random number            
            # datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Output: '2025-05-14 15:30:45'
            # order_number = f"{timezone.now().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"
            current_user = request.user   # if user is not authenticated, its an instance of AnonymousUser, not None.

            order = Order.objects.create(
                user=current_user,
                mobile=current_user.mobile,  # request.POST.get("mobile") -- if from form data
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
			# session key is in Cart if needed
            for cart_item in cart_products:
                OrderProduct.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    product_price=cart_item.product.price,
                )

                product = Product.objects.get(id=cart_item.product.id)
                if product.stock >= cart_item.quantity:
                    product.stock -= cart_item.quantity
                    product.save()

            send_order_confirmation_email(current_user, order)  # only if logged in

            if payment_option == "cash":
                cart_products.delete()
                #return redirect("order_complete")  # ---- Reverse for 'order_complete' not found.
                return HttpResponse("<h3>Your payment is successful</h3>") # ------------------------------------------------------------------------------------------------------------
            elif payment_option == "sslcommerz":
                return redirect("payment")
        # edge cases: user added products to orders but payment was unsuccessful, then avaiable quantity fix.
		# see: django cron job
        except Exception as e:
            return HttpResponse("Error occurred: " + str(e))

    #
    context = {
        "total_price": total_price,
        "quantity": quantity,
        "cart_items": cart_products,
        "cart_count": quantity,        
        "grand_total": total_price + getattr(settings, 'DELIVERY_CHARGE', 0),
    }    
    return render(request, "orders/checkout.html", context)


#@login_required
def payment(request):
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
        # TODO: restock product
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
        # save to Payment class ?
        #order = Order.objects.filter(user=request.user, is_ordered=False).last()
        order = Order.objects.filter(user=request.user, status="Pending").last()  # -----------------
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
        
        #Cart.objects.filter(user=request.user).last().delete()  # delete last one
        Cart.objects.filter(user=request.user).delete() # delete all

        context = {
            "order": order,
            "transaction_id": tran_id,
        }
        return render(request, "orders/status.html", context)  # order success

    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500)