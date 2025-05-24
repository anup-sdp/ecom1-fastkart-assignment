# products, models

from django.db import models
from django.utils.text import slugify
from accounts.models import CustomUser
from django.db.models import Avg, Count
from django.core.validators import MinValueValidator, MaxValueValidator

from django.utils import timezone
import datetime

class TimeStampedModel(models.Model): # this model is not created in database, as abstract
    """
    An abstract base class model that provides self-managed "created_at" and
    "updated_at" fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    # A slug is a URL-friendly version of a string, typically used in web development to create readable URLs.
    # models.SlugField is a field type in Django that's specifically designed to store slugs.
    image = models.ImageField(upload_to="categories")  # MEDIA_ROOT/categories/

    def save(self, *args, **kwargs):       
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.name}"
    

class Product(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True) # used insted of id in url, multiple same name ? ----------------------
    description = models.TextField(blank=True)
    #price = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # prefered for price
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    unit = models.CharField(max_length=100, null=True, blank=True)
    rating = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, null=True, blank=True
    )
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE) # if models.SET_NULL, null = True needed, 
    # here user wont provide related_name
    # Forward relation: product.category  # Gets the Category object for this product
    # Reverse relation: category.products.all()  # Gets all products (list) in this category
    
    def is_new(self):
        return self.updated_at >= timezone.now() - datetime.timedelta(days=7)
    
    def save(self, *args, **kwargs):
        #self.slug = slugify(self.name)
        #super().save(*args, **kwargs)        
        if not self.slug:   # Generate slug only if not provided
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def discount_price(self):
        return self.price * (100 - self.discount_percentage)/100

    @property
    def savings(self):
        """Calculate the savings by subtracting the discount price from the original price."""
        return self.price - self.discount_price

    def get_discounted_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def averageReview(self):
        reviews = Review.objects.filter(product=self, status=True).aggregate(
            average=Avg("rating")
        )
        avg = 0
        if reviews["average"] is not None:
            avg = float(reviews["average"])
        self.rating = avg
        return avg
    
    # @property
    def count_review(self):
        reviews = Review.objects.filter(product=self, status=True).aggregate(
            count=Count("id")
        )
        count = 0
        if reviews["count"] is not None:
            count = int(reviews["count"])
        return count
    
"""
create product example:
# Get a category (e.g., "Electronics")
electronics_category = Category.objects.get(name="Electronics")

# Create a new product linked to that category
new_product = Product.objects.create(
    name="Smartphone",
    price=699.99,
    category=electronics_category,  # Assign the category directly
    # ... other fields
)
"""    

"""
# without related_name, get all products of a category
# Get a category
electronics = Category.objects.get(category_name="Electronics")

# Get all products in this category (reverse lookup)
products_in_category = electronics.product_set.all() # Django's default related_name is [model_name]_set
"""

class Review(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews")
    rating = models.FloatField()
    # rating = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],)
    review = models.TextField()
    is_approved = models.BooleanField(default=True)  # instead of status used in main github
    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"
    


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)  # in db product_id is created.
    image = models.ImageField(upload_to="products/images")  # MEDIA_ROOT/products/images/
    # In production, you should never serve files directly via Django - use a web server (Nginx/Apache) or cloud storage (AWS S3)
    def __str__(self):
        return f"{self.pk}. Image for {self.product.name}"

"""
# First get the product named "potato"
potato = Product.objects.get(name="potato")

# Then access all its images using the related_name "images"
potato_images = potato.images.all()  # Uses the related_name
# images = product.productimage_set.all()  # Default: [modelname]_set  # only use if you didn't specify related_name
"""

"""
images = ProductImage.objects.filter(product__name="potato")
# OR
images = Product.objects.get(name="potato").images.all()

"""