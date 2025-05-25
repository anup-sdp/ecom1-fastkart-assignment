# products, views.py
from django.shortcuts import render
from .models import Product
from django.http import HttpResponse

from .models import Category, Product, Review

from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator  # ---------------------

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .forms import ReviewForm

from django.utils import timezone
from datetime import timedelta


from django.urls import reverse
from django.db.models import Avg, Count
from carts.utils import get_session_key
from carts.models import Cart, CartProduct

def home(request):
    #return HttpResponse("<h3>homepage is under construction!</h3>")
    products = Product.objects.all()
    #categories = Category.objects.all()
    categories = Category.objects.annotate(product_count=Count("products"))  # adds product_count to Category for this object
    """
    python manage.py shell
    from django.db.models import Count
    from products.models import Category
    print(Category.objects.annotate(product_count=Count("products")).query)    # see raw sql django orm generates under the hood
    """	
    
    """
    # Add new arrival flag to products / alternate to using is_new() in Products class
    current_time = timezone.now()
    for product in products:
        product.is_new_arrival = (current_time - product.updated_at).days <= 7
    """    
    # seven_days_ago = timezone.now() - timedelta(days=7)    
    # For better performance with large datasets, prefer the database annotation     

    context = {"products": products, "categories": categories}
    
    return render(request, 'products/home.html', context)
    

def category_products(request, category_slug):
    #category = Category.objects.get(slug= category_slug)
    category = get_object_or_404(Category, slug=category_slug)    
    products = Product.objects.filter(category=category)
    paginator = Paginator(products, 2)  # search -----------------------------------
    page = request.GET.get("page")
    paged_products = paginator.get_page(page)  # ------------

    context = {
        "products": paged_products,
        "category": category,
    }
    return render(request, "products/category_products.html", context)


def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    #reviews = product.reviews.filter(status=True)  # status used in main github
    reviews = product.reviews.filter(is_approved=True)  # Corrected from status to is_approved
    # removed each star count
    # Calculate rating counts and average
    rating_counts = reviews.count()
    average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0
    average_rating = round(average_rating, 1) # 1 decimal digit after point    
    
    cart = None
    quantity_in_cart = 0
    session_key=get_session_key(request) # this part copied from carts.views
    if request.user.is_authenticated:                   
        cart = Cart.objects.filter(user=request.user).last()
        if cart == None:
            cart = Cart.objects.create(user=request.user)  # Handle missing object (e.g., create a new Cart)        
    else:        
        cart, created = Cart.objects.get_or_create(session_key=session_key, defaults={'user': None})
    # cart_items = CartProduct.objects.filter(cart=cart).select_related("product") # list of CartProduct items, get quantity
    if cart:            
        cart_product = CartProduct.objects.filter(cart=cart, product=product).first()  # returns None, if no match
        if cart_product:
            quantity_in_cart = cart_product.quantity           
    
    context = {
        "product": product,
        "quantity_in_cart": quantity_in_cart, #  Updated dynamically
        "rating_counts": rating_counts,
        'average_rating':average_rating,
        "reviews": reviews,
    }
    return render(request, "products/product-left-thumbnail.html", context)



@require_POST
@login_required
def submit_review(request, product_slug):  # in file product-left-thumbnail.html, form at line 1466
    url = request.META.get("HTTP_REFERER", "") or reverse("home")  # url which called, after task return there
    try:
        # update existing review
        review = Review.objects.get(user__id=request.user.id, product__slug=product_slug)
        form = ReviewForm(request.POST, instance=review)
        form.save()
        messages.success(request, "Thank you! Your review has been updated.")
        return redirect(url)
    except Review.DoesNotExist:
        # create new review
        form = ReviewForm(request.POST)
        if form.is_valid():
            """
            data = Review()
            data.product = Product.objects.get(slug=product_slug)
            data.user_id = request.user.id
            data.rating = form.cleaned_data["rating"]
            data.review = form.cleaned_data["review"]
            data.save()
            """
            review = form.save(commit=False)
            review.product = Product.objects.get(slug=product_slug)
            review.user = request.user
            review.save()            
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect(url)
        else:
            # messages.info(request, "sorry, form is invalid!")
            # messages.error(request, f"Form errors: {form.errors}")  # containing all validation errors
            #for field, errors in form.errors.items():
            #    messages.error(request, f"{field}: {', '.join(errors)}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect(url)



"""
def potato_images(request):  # not needed
    try:
        potato = Product.objects.get(name="potato")
        images = potato.images.all()  # Using the related_name
        return render(request, 'products/potato_images.html', {'images': images})
    except Product.DoesNotExist:        
        return HttpResponse("<h3>product potato not found!</h3>")
"""