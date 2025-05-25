# products, urls.py
from django.urls import path
from . import views


"""
# app_name = 'products'  # Optional namespace
<!-- landing-page.html -->
<a href="{% url 'products:potato_images' %}">
    <button>Potato Product Images</button>
</a>
"""

urlpatterns = [    
	path("", views.home, name="home"),
	path("products/<slug:product_slug>/", views.product_detail, name="product_detail"),  # http://127.0.0.1:8000/products/potato/
	path("categories/<slug:category_slug>/products", views.category_products, name="category_products",),	
    path("products/<slug:product_slug>/submit-review/", views.submit_review, name="submit_review",),	  
	# path('potato-images/', views.potato_images, name='potato_images'), # for testing only
]

