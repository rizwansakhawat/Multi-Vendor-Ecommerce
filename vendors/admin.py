from django.contrib import admin
from .models import VendorProfile, VendorPayout, VendorTransaction


class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'shop_slug', 'user_email', 'total_sales', 'total_orders', 'average_rating', 'total_reviews')
    search_fields = ('shop_name', 'shop_slug', 'user__email')
    readonly_fields = ('shop_slug',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
class VendorPayoutAdmin(admin.ModelAdmin):  
    list_display = ['vendor', 'amount', 'status', 'payout_date', 'created_at']
    search_fields = ('vendor__shop_name', 'order_id')
    
    def payout_status(self, obj):
        if obj.payout:
            return obj.payout.status
        return 'N/A'
    payout_status.short_description = 'Payout Status'   
    
class VendorTransactionAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'transaction_type', 'net_amount', 'commission_amount', 'transaction_date')
    search_fields = ('vendor__shop_name', 'order_id')   
    
admin.site.register(VendorProfile, VendorProfileAdmin)
admin.site.register(VendorPayout, VendorPayoutAdmin)    
admin.site.register(VendorTransaction, VendorTransactionAdmin)


