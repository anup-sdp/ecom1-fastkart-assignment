from django.contrib import admin

from .models import Order, OrderProduct, Payment

admin.site.register([Order, OrderProduct, Payment])
