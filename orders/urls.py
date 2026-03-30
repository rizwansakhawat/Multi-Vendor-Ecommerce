
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, CartViewSet, CartItemViewSet


router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')          
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')    

urlpatterns = [
    path('', include(router.urls)), 
]   
