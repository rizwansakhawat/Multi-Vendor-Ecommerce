from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin','Admin'),
        ('vendor','Vendor'),
        ('buyer','Buyer')
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)   
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    def __str__(self):
        return f"{self.email} - {self.role}"
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'   
        
    
class Address(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100  )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.state}, {self.country}"
    
    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        
        
    
    

