# products, views.py
from django.shortcuts import render
from .models import Product
from django.http import HttpResponse

from .models import Category, Product, Review
from django.db.models import Count

from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator  # ---------------------

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .forms import ReviewForm


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
    """
    rating_counts = {
        "5": product.reviews.filter(rating__gt=4.4, rating__lte=5.1).count(),
        "4": product.reviews.filter(rating__gt=3.4, rating__lte=4.1).count(),
        "3": product.reviews.filter(rating__gt=2.4, rating__lte=3.1).count(),
        "2": product.reviews.filter(rating__gt=1.4, rating__lte=2.1).count(),
        "1": product.reviews.filter(rating__gt=0.4, rating__lte=1.1).count(),
    }

    total_reviews = sum(rating_counts.values())

    rating_percentages = {
        "5": (rating_counts["5"] / total_reviews * 100) if total_reviews else 0,
        "4": (rating_counts["4"] / total_reviews * 100) if total_reviews else 0,
        "3": (rating_counts["3"] / total_reviews * 100) if total_reviews else 0,
        "2": (rating_counts["2"] / total_reviews * 100) if total_reviews else 0,
        "1": (rating_counts["1"] / total_reviews * 100) if total_reviews else 0,
    }
    """
    context = {
        "product": product,
        "rating_counts": 0,
        "rating_percentages": 0,
        'average_review':0,
        'count_review':0,
        "reviews": reviews,
    }
    return render(request, "products/product-left-thumbnail.html", context)



@require_POST
@login_required
def submit_review(request, product_slug):  # in file product-left-thumbnail.html, form at line 1466
    url = request.META.get("HTTP_REFERER")  # url which called, after task return there
    try:
        # update existing review
        review = Review.objects.get(
            user__id=request.user.id, product__slug=product_slug
        )
        form = ReviewForm(request.POST, instance=review)
        form.save()
        messages.success(request, "Thank you! Your review has been updated.")
        return redirect(url)
    except Review.DoesNotExist:
        # create new review
        form = ReviewForm(request.POST)
        if form.is_valid():
            # data = Review()
            # data.product = Product.objects.get(slug=product_slug)
            # data.user_id = request.user.id
            # data.rating = form.cleaned_data["rating"]
            # data.review = form.cleaned_data["review"]
            # data.save()
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


def remove_cart(request, product_slug):
    # Add logic to remove item from cart
    return redirect('category_products', category_slug=request.GET.get('category_slug', ''))

def add_cart(request, product_slug):
    # Add logic to add item to cart
    return redirect('category_products', category_slug=request.GET.get('category_slug', ''))


def potato_images(request):  # not needed
    try:
        potato = Product.objects.get(name="potato")
        images = potato.images.all()  # Using the related_name
        return render(request, 'products/potato_images.html', {'images': images})
    except Product.DoesNotExist:        
        return HttpResponse("<h3>product potato not found!</h3>")
