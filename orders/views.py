from decimal import Decimal

from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer
from rest_framework import status, viewsets
from accounts.permission import IsVendor, IsAdminOrVendorOwner, IsBuyer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .tasks import send_order_created_email



class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)    
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'admin':
            return Order.objects.all()
        if getattr(user, 'role', None) == 'vendor':
            if not hasattr(user, 'vendor_profile'):
                return Order.objects.none()
            return Order.objects.filter(orderitem__product__vendor=user.vendor_profile).distinct()
        
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        send_order_created_email.delay(order.id)

    @action(detail=False, methods=['post'], url_path='create-from-cart')
    def create_from_cart(self, request):
        cart_id = request.data.get('cart_id')
        if not cart_id:
            raise ValidationError({'cart_id': 'cart_id is required.'})

        try:
            cart = Cart.objects.prefetch_related('cartitem_set__product').get(pk=cart_id, user=request.user)
        except Cart.DoesNotExist:
            raise ValidationError({'cart_id': 'Cart not found.'})

        cart_items = list(cart.cartitem_set.all())
        if not cart_items:
            raise ValidationError({'cart_id': 'Your cart is empty.'})

        total_price = sum(
            (Decimal(item.product.price) * item.quantity for item in cart_items),
            start=Decimal('0.00'),
        )

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                status='pending',
            )

            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                for item in cart_items
            ])

            # Move checkout items out of cart once order rows are created.
            cart.cartitem_set.all().delete()

        send_order_created_email.delay(order.id)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
            
    
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)    
    
