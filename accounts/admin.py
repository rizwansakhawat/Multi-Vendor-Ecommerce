from django.contrib import admin
from .models import User, Address
from django.contrib.auth.admin import UserAdmin


# Register your models here.

class CustomUserAdmin(UserAdmin):

    model = User
    list_display = ('email', 'username', 'role', 'email_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'email_verified', 'is_staff', 'is_active', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login','date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role', 'email_verified', 'is_staff', 'is_active', 'is_superuser')}
         ),
    )
    search_fields = ('email','username ', 'first_name', 'last_name ')
    ordering = ('email',)
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(Address)