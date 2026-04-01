from warnings import filters

from django.shortcuts import render
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer  
from rest_framework import generics, permissions, viewsets
from accounts.permission import IsVendor, IsAdminOrVendorOwner, IsBuyer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser | IsVendor]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()
    
    
    
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'vendor']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser | IsVendor]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()
    
    def get_queryset(self):
        if self.action == 'list':
            return Product.objects.filter(status=True)
        return Product.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user.vendorprofile) 
    
    
        