# context_processors for global cart_count
# cons: can be db lookup for all pages (cache solution?), multiple cart creations ?
from django.db.models import Sum
from .models import Cart, CartProduct

def cart_context(request):
    cart_count = 0
    cart = None

    if request.user.is_authenticated:       
        cart = Cart.objects.filter(user=request.user).last()
        if not cart:
            cart = Cart.objects.create(user=request.user)
    else:      
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key        
    
        cart = Cart.objects.filter(session_key=session_key).last()      
        if not cart:
            cart = Cart.objects.create(session_key=session_key)
   
    if cart:
        result = cart.cart_products.aggregate(total=Sum('quantity'))  # returns dictionary        
        cart_count = result.get('total', 0) or 0  # cart_count = result['total'] or 0

    return {'cart_count': cart_count}
