from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User

class VendorProfile(models.Model):

    user = models.OneToOneField(User,on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=200)
    shop_slug = models.SlugField(unique=True)
    shop_logo = models.ImageField(upload_to='shops/', blank=True, null=True)
    shop_banner = models.ImageField(upload_to='shops/', blank=True, null=True)
    shop_description = models.TextField(max_length=1000, blank=True)
    
    
    commission_rate = models.FloatField(
        default=settings.PLATFORM_COMMISSION_PERCENTAGE,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    # Statistics
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    featured_vendor = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    
    class Meta:
        db_table = 'vendor_profile'
        verbose_name = 'Vendor' 
        verbose_name_plural = 'Vendors'  
    
    def __str__(self):
        return self.shop_name
    
    def calculate_commission(self, sale_amount):
        return (sale_amount * self.commission_rate) / 100
    
    def update_stats(self):
        from orders.models import OrderItem
        from reviews.models import Review
        
        self.total_sales = OrderItem.objects.filter(product__vendor=self).aggregate(total=models.Sum('total_price'))['total'] or 0
        self.total_orders = OrderItem.objects.filter(product__vendor=self).count()
        self.average_rating = Review.objects.filter(product__vendor=self).aggregate(average=models.Avg('rating'))['average'] or 0
        self.total_reviews = Review.objects.filter(product__vendor=self).count()
        self.save()


    
    
class VendorPayout(models.Model):
    choices = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    comission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='pending', choices=choices)  
    
    pyment_method = models.CharField(max_length=50, blank=True, null=True)
    trancation_id = models.CharField(max_length=100, blank=True, null=True)
    payout_date = models.DateTimeField(auto_now_add=True)
    
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_payout'
        verbose_name = 'Vendor Payout' 
        verbose_name_plural = 'Vendor Payouts'  
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payout of {self.amount} to {self.vendor.shop_name} on {self.payout_date.strftime('%Y-%m-%d')}"



class VendorTransaction(models.Model):
    choice=[
        ('sale', 'Sale'),   
        ('refund', 'Refund'),
        ('payout', 'Payout'),
        ('commission', 'Commission'),]
    
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=choice)
    order_id = models.CharField(max_length=100)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    payout = models.ForeignKey(VendorPayout, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions')

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vendor_transaction'
        verbose_name = 'Vendor Transaction' 
        verbose_name_plural = 'Vendor Transactions'  
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type}-{self.amount} for {self.vendor.shop_name} on {self.transaction_date.strftime('%Y-%m-%d')}"

