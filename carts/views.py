from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .models import Cart, CartProduct
from .utils import get_session_key


def add_cart(request, product_slug):  # add a product to cart
    product = get_object_or_404(Product, slug=product_slug)
    try:
        cart = Cart.objects.get(session_key=get_session_key(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            user= request.user,  # an instance of AnonymousUser if the user is not authenticated
            session_key=get_session_key(request)
        )

    try:        
        cart_item = CartProduct.objects.get(product=product, cart=cart)  # if product already exists in cart
    except CartProduct.DoesNotExist:
        cart_item = CartProduct(
            product=product,
            cart=cart,            
            quantity=0,
        )

    cart_item.quantity += 1
    cart_item.save()
    
	
    url = request.META.get("HTTP_REFERER")  # to go back to calling url
    return redirect(url)
	# return redirect(request.path) -- ?	
	# search: update the cart item quantity via AJAX so the page doesn’t reload



def remove_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    if request.user.is_authenticated:
        #cart = get_object_or_404(Cart, user=request.user)
        cart = Cart.objects.filter(user=request.user).order_by('-created_at').first()
    else:
        cart = get_object_or_404(Cart, session_key=get_session_key(request))

    cart_item = get_object_or_404(CartProduct, product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    url = request.META.get("HTTP_REFERER")   # Could be None
    return redirect(url)
    #return redirect(url or "cart_detail")   # Fallback to "cart_detail" if url is None


def cart_detail(request, total_price=0, quantity=0, cart_items=None):
    session_key=get_session_key(request)
    if request.user.is_authenticated:
        #cart = get_object_or_404(Cart, user=request.user) # disabled to not see Page not found (404), when user has no cart.
        # cart, created = Cart.objects.get_or_create(user=request.user, defaults={'session_key': session_key})  # returns tuple. # problem for multiple carts
        """"""
        try:
            #cart = Cart.objects.get(user=request.user).last()  # expects only 1, error if multiple
            cart = Cart.objects.filter(user=request.user).last()
        except Cart.DoesNotExist:    
            cart = Cart.objects.create(user=request.user)  # Handle missing object (e.g., create a new Cart)
        
    else:
        #cart = get_object_or_404(Cart, session_key=session_key)
        cart, created = Cart.objects.get_or_create(session_key=session_key, defaults={'user': None})
    # cart_items = CartProduct.objects.filter(cart=cart) # causes n+1 problem, inefficient for database query
    cart_items = CartProduct.objects.filter(cart=cart).select_related("product")  # "product" is field name, not related_name  # rename to cart_products
    # ^ here, Django fetches all CartProduct objects and their related Product objects in a single query using a SQL JOIN.
    # using select_related avoids n+1 problem, (for ForeignKey/OneToOne) or prefetch_related (for ManyToMany or reverse ForeignKeys).
    # select_related follows forward relationships (from the model you’re querying to related models),
    # but related_name="cart_products" is for reverse relations (ie. Product.objects.prefetch_related('cart_products')), so it's not used here. 
    total_price = 0
    for item in cart_items:
        dp = (100-item.product.discount_percentage)/100  # discount_percentage -> dp, 10% -> 0.9
        total_price += item.product.price * dp * item.quantity 
        quantity += item.quantity

    context = {
        "total_price": total_price,
        "quantity": quantity,
        "cart_items": cart_items,
        "cart_count": quantity,
        # "grand_total": total_price + settings.DELIVERY_CHARGE,        
        "shipping_price": getattr(settings, 'DELIVERY_CHARGE', 0),
        "grand_total": total_price + getattr(settings, 'DELIVERY_CHARGE', 0),  # extend + add tax etc
        # add cupon discount ?
    }
    return render(request, "carts/cart.html", context)

