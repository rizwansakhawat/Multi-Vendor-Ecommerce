from django.contrib import admin

from .models import Product, Category, ProductImage
from django.utils.html import format_html


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Image Preview'
    


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    
    
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'category', 'price', 'stock', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'category']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)  

    
    
