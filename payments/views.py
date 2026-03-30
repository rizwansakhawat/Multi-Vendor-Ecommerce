from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from orders.models import Order

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		base_queryset = Payment.objects.all().order_by('-created_at')

		if user.role == 'admin':
			return base_queryset

		if user.role == 'vendor':
			vendor_order_ids = Order.objects.filter(
				orderitem__product__vendor__user=user
			).values_list('id', flat=True)
			return base_queryset.filter(order_id__in=[str(order_id) for order_id in vendor_order_ids])

		buyer_order_ids = Order.objects.filter(user=user).values_list('id', flat=True)
		return base_queryset.filter(order_id__in=[str(order_id) for order_id in buyer_order_ids])

	def perform_create(self, serializer):
		user = self.request.user
		order_id = serializer.validated_data.get('order_id')

		try:
			order = Order.objects.get(pk=order_id)
		except (Order.DoesNotExist, ValueError, TypeError):
			raise ValidationError({'order_id': 'Order not found.'})

		if user.role == 'buyer' and order.user_id != user.id:
			raise PermissionDenied('You can only pay for your own order.')

		if user.role == 'vendor':
			is_vendor_order = order.orderitem_set.filter(product__vendor__user=user).exists()
			if not is_vendor_order:
				raise PermissionDenied('You do not have access to this order payment.')

		serializer.save(order_id=str(order.id), amount=order.total_price)
