from django.db import models

from accounts.models import CustomUser
from products.models import Product, TimeStampedModel

class Cart(TimeStampedModel):
    # user = models.ForeignKey(CustomUser, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, null=True, related_name="carts", on_delete=models.CASCADE)  # each user can have 1 cart, null=True, for non-user's Cart
    # user = models.OneToOneField(CustomUser, null=True, on_delete=models.CASCADE, related_name='carts')
    session_key = models.CharField(max_length=255, null=True, blank=True) # now optional,  unique=True if each session should have at most one cart?
    
    # has created_at and updated_at from TimeStampedModel
    def __str__(self):
        return  f"{self.session_key}"  # was getting None
    # status = [open, submitted, abandoned, cancelled]


class CartProduct(TimeStampedModel):  # was CartItem
    cart = models.ForeignKey(Cart, related_name="cart_products", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_products", on_delete=models.CASCADE, null=True)  # on_delete=models.DO_NOTHING
    quantity = models.PositiveSmallIntegerField(default=0)

    def sub_total(self):
        return self.product.discount_price * self.quantity

    def __str__(self):
        return f"CartItem: {self.product.name}"

