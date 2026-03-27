from rest_framework import serializers
from .models import VendorProfile, VendorPayout, VendorTransaction 
from accounts.serializers import UserSerializer

class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    earnings = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorProfile
        fields = '__all__'
        read_only_fields = ['user', 'total_sales', 'total_orders', 'average_rating', 'total_reviews']
        
    def get_earnings(self, obj):
        from django.db.models import Sum
        
        # Sum all completed sales
        total_earned = obj.transactions.filter(
            transaction_type='SALE'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        # Subtract payouts
        total_paid = obj.transactions.filter(
            transaction_type='PAYOUT'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        return {
            'total_earned': total_earned,
            'total_paid': total_paid,
            'available_balance': total_earned - total_paid
        }
        
        
        
class VendorProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = ['shop_name', 'shop_description', 'shop_slug', 'shop_banner',
                  'shop_logo','shop_description']
        
    def validate_shop_slug(self, value):
        if VendorProfile.objects.filter(shop_slug=value).exists():
            raise serializers.ValidationError("Shop slug already exists")
        return value
    
class VendorPayoutSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = VendorPayout
        fields = '__all__'
        read_only_fields = ['vendor', 'created_at', 'updated_at']
        
        
class VendorTransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = VendorTransaction
        fields = '__all__'
        read_only_fields = ['vendor', 'created_at']
        
        
        
class VendorDashboardSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_orders = serializers.IntegerField(read_only=True)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    pending_orders = serializers.IntegerField(read_only=True)
    available_balance = serializers.SerializerMethodField()
    recent_orders = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    
