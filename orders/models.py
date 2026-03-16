from django.db import models
from django.conf import settings
from products.models import Product

User = settings.AUTH_USER_MODEL


class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)

class CartItem(models.Model):

    cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    
    
    
class Order(models.Model):

    STATUS = (
        ('pending','Pending'),
        ('paid','Paid'),
        ('shipped','Shipped'),
        ('delivered','Delivered')
    )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)