from django.db import models
from products.models import Product, TimeStampedModel
from accounts.models import CustomUser



class Payment(TimeStampedModel):
    user = models.ForeignKey(CustomUser, null=True, related_name="payments", on_delete=models.SET_NULL)
    payment_id = models.CharField(null=True, blank=True, max_length=255)  # this id is sent from sslcommerz , it's not database id
    payment_method = models.CharField(null=True, blank=True, max_length=255)  # cash/ sslcommerz     
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(null=True, max_length=255)  # pending/paid/failed etc



class Order(TimeStampedModel):
    """
    STATUS = (
        ("New", "New"),
        ("Accepted", "Accepted"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    )
	"""
    user = models.ForeignKey(CustomUser, null=True, related_name="orders", on_delete=models.SET_NULL)  # can have order without user.
    payment = models.ForeignKey(Payment, null=True, on_delete=models.CASCADE)        
    
    order_number = models.CharField(null=True, blank=True, max_length=255)
    order_note = models.CharField(null=True, blank=True, max_length=255)
    
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(null=True, max_length=255, default="Pending")  # pending/Pending, Failed,
    
    address_line_1 = models.CharField(null=True, blank=True, max_length=100)  # copied from CustomUser
    address_line_2 = models.CharField(null=True, blank=True, max_length=100)
    city = models.CharField(blank=True, max_length=20)
    postcode = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20) 
    mobile = models.CharField(null=True, blank=True, max_length=15) 
    # email ? ------------
    # session key ? -------- has in Cart

    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"
	



class OrderProduct(TimeStampedModel):
    order = models.ForeignKey(Order, related_name="order_products", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_products", on_delete=models.CASCADE, null=True)  # on_delete=models.DO_NOTHING
    quantity = models.PositiveSmallIntegerField(default=0)
    product_price = models.DecimalField(max_digits=10, decimal_places=2) # price when bought, can be different from product table price
    def __str__(self):
        return self.product.name

    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, blank=True, null=True
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered = models.BooleanField(default=False)

    
	"""