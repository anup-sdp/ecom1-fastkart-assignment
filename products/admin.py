
"""
from django.contrib import admin
from .models import Category, Product, ProductImage, Review
admin.site.register([Category, Product, ProductImage, Review])
"""

from django.contrib import admin
from .models import Category, Product, ProductImage, Review
from django.utils.html import format_html

class ProductImageInline(admin.TabularInline):  # or admin.StackedInline
    model = ProductImage
    extra = 1  # how many blank image slots to show
    # readonly_fields = ()  # if you wanted to show thumbnails, you could add a method here
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;"/>', obj.image.url)
        return "No Image"
    readonly_fields = ('image_preview',)
    image_preview.short_description = 'Preview'
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug from name
    # list_display = ("name", "price", "stock", "available", "category")
    # list_filter  = ("available", "category")
    # search_fields = ("name",)
    
""""""
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "image_preview")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;"/>', obj.image.url)
        return "No Image"

    image_preview.short_description = 'Preview'


# Keep other registrations as-is
admin.site.register([Review])