from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Vendor(models.Model):

    user = models.OneToOneField(User,on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=200)
    shop_logo = models.ImageField(upload_to='shops/')
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.shop_name