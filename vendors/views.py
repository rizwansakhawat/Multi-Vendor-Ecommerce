from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from .models import VendorProfile, VendorPayout, VendorTransaction
from .serializers import VendorProfileSerializer, VendorProfileCreateSerializer, VendorPayoutSerializer, VendorTransactionSerializer, VendorDashboardSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta  

from accounts.permission import IsVendor, IsAdminOrVendorOwner

class VendorRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if hasattr(request.user, 'vendor_profile'):
            return Response({"detail": "User already has a vendor profile"}, status=status.HTTP_400_BAD_REQUEST)    
        serializer = VendorProfileCreateSerializer(data=request.data)
        if serializer.is_valid():
            vendor_profile = serializer.save(user=request.user)
            return Response(VendorProfileSerializer(vendor_profile).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrVendorOwner]
    
    def get_object(self):
        return get_object_or_404(VendorProfile, user=self.request.user)
    
    
class VendorDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get(self, request):
        vendor = request.user.vendor_profile
        from products.models import Product
        from orders.models import Order, OrderItem
        
        # Calculate statistics
        total_products = Product.objects.filter(vendor=vendor).count()
        
        pending_orders = Order.objects.filter(
            items__product__vendor=vendor,
            status='PENDING'
        ).distinct().count()
        
        # Calculate available balance
        total_earned = vendor.transactions.filter(
            transaction_type='SALE'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        total_paid = vendor.transactions.filter(
            transaction_type='PAYOUT'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        available_balance = total_earned - total_paid
        
        # Recent transactions
        recent_transactions = vendor.transactions.all()[:10]
        
        # Recent orders for this vendor
        recent_orders_data = []
        recent_orders = Order.objects.filter(
            items__product__vendor=vendor
        ).distinct().order_by('-created_at')[:5]
        
        for order in recent_orders:
            order_items = order.items.filter(product__vendor=vendor)
            recent_orders_data.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_name': f"{order.user.first_name} {order.user.last_name}",
                'total': sum(item.price * item.quantity for item in order_items),
                'status': order.status,
                'created_at': order.created_at
            })
        
        data = {
            'total_sales': vendor.total_sales,
            'total_orders': vendor.total_orders,
            'average_rating': vendor.average_rating,
            'total_products': total_products,
            'pending_orders': pending_orders,
            'available_balance': available_balance,
            'recent_transactions': VendorTransactionSerializer(recent_transactions, many=True).data,
            'recent_orders': recent_orders_data
        }
        
        serializer = VendorDashboardSerializer(data)
        return Response(serializer.data)
    

class VendorPayoutViewSet(viewsets.ModelViewSet):
    serializer_class = VendorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get_queryset(self):
        return VendorPayout.objects.filter(vendor=self.request.user.vendor_profile)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get payout history with statistics"""
        vendor = request.user.vendor_profile
        payouts = self.get_queryset()
        
        total_paid = payouts.filter(status='COMPLETED').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        pending_payouts = payouts.filter(status='PENDING').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        data = {
            'total_paid': total_paid,
            'pending_payouts': pending_payouts,
            'payouts': self.get_serializer(payouts, many=True).data
        }
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def request_payout(self, request):
        """Request a new payout"""
        vendor = request.user.vendor_profile
        
        # Calculate available balance
        total_earned = vendor.transactions.filter(
            transaction_type='SALE'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        total_paid = vendor.transactions.filter(
            transaction_type='PAYOUT'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        available_balance = total_earned - total_paid
        
        if available_balance <= 0:
            return Response(
                {'error': 'No available balance for payout'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for pending payout requests
        if VendorPayout.objects.filter(
            vendor=vendor,
            status__in=['PENDING', 'PROCESSING']
        ).exists():
            return Response(
                {'error': 'You already have a pending payout request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payout request
        payout = VendorPayout.objects.create(
            vendor=vendor,
            amount=available_balance,
            commission_amount=0,  # No commission on payout
            net_amount=available_balance,
            period_start=timezone.now() - timedelta(days=30),
            period_end=timezone.now(),
            notes='Auto-generated payout request'
        )
        
        return Response(
            VendorPayoutSerializer(payout).data,
            status=status.HTTP_201_CREATED
        )