from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permission import IsBuyer
from orders.models import OrderItem

from .models import Review
from .serializers import ReviewSerializer


class IsReviewOwnerOrAdmin(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		return request.user.role == 'admin' or obj.user_id == request.user.id


class ReviewViewSet(viewsets.ModelViewSet):
	serializer_class = ReviewSerializer
	queryset = Review.objects.select_related('user', 'product').all().order_by('-created_at')

	def get_permissions(self):
		if self.action in ['list', 'retrieve']:
			return [permissions.AllowAny()]
		if self.action == 'create':
			return [permissions.IsAuthenticated(), IsBuyer()]
		return [permissions.IsAuthenticated(), IsReviewOwnerOrAdmin()]

	def get_queryset(self):
		queryset = super().get_queryset()
		product_id = self.request.query_params.get('product')
		if product_id:
			queryset = queryset.filter(product_id=product_id)
		return queryset

	def perform_create(self, serializer):
		user = self.request.user
		product = serializer.validated_data['product']

		has_purchased = OrderItem.objects.filter(
			order__user=user,
			product=product,
			order__status__in=['paid', 'shipped', 'delivered'],
		).exists()

		if not has_purchased:
			raise PermissionDenied('You can only review products you have purchased.')

		if Review.objects.filter(user=user, product=product).exists():
			raise ValidationError('You have already reviewed this product.')

		serializer.save(user=user)
