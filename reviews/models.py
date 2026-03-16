from django.db import models
from products.models import Product
from django.conf import settings

User = settings.AUTH_USER_MODEL

# Create your models here.
class Review(models.Model):

    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    rating = models.IntegerField()
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)