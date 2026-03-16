from django.db import models
from vendors.models import Vendor


# Create your models here.
class Product(models.Model):
    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name