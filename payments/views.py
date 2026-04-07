from decimal import Decimal, ROUND_HALF_UP
import json
from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.tasks import send_order_paid_email

from .models import Payment
from .serializers import PaymentSerializer

try:
	import stripe
except ImportError:
	stripe = None


class PaymentViewSet(viewsets.ModelViewSet):
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]

	def _get_accessible_order(self, user, order_id):
		try:
			order = Order.objects.get(pk=order_id)
		except (Order.DoesNotExist, ValueError, TypeError):
			raise ValidationError({'order_id': 'Order not found.'})

		if user.role == 'buyer' and order.user_id != user.id:
			raise PermissionDenied('You can only pay for your own  .')

		if user.role == 'vendor':
			is_vendor_order = order.orderitem_set.filter(product__vendor__user=user).exists()
			if not is_vendor_order:
				raise PermissionDenied('You do not have access to this order payment.')

		return order

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
		order = self._get_accessible_order(user, order_id)

		serializer.save(order_id=str(order.id), amount=order.total_price)

	@action(detail=False, methods=['post'], url_path='stripe/checkout-session')
	def create_stripe_checkout_session(self, request):
		if stripe is None:
			raise ValidationError({'detail': 'Stripe SDK not installed. Install stripe package.'})

		order_id = request.data.get('order_id')
		if not order_id:
			raise ValidationError({'order_id': 'order_id is required.'})

		order = self._get_accessible_order(request.user, order_id)

		if order.status == 'paid':
			raise ValidationError({'detail': 'This order is already paid.'})

		if not settings.STRIPE_SECRET_KEY:
			raise ValidationError({'detail': 'STRIPE_SECRET_KEY is not configured.'})

		stripe.api_key = settings.STRIPE_SECRET_KEY
		amount_in_cents = int((Decimal(order.total_price) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

		success_url = settings.STRIPE_SUCCESS_URL
		cancel_url = settings.STRIPE_CANCEL_URL

		session = stripe.checkout.Session.create(
			mode='payment',
			payment_method_types=['card'],
			line_items=[
				{
					'price_data': {
						'currency': settings.STRIPE_CURRENCY,
						'unit_amount': amount_in_cents,
						'product_data': {'name': f'Order #{order.id}'},
					},
					'quantity': 1,
				}
			],
			success_url=success_url,
			cancel_url=cancel_url,
			metadata={
				'order_id': str(order.id),
				'user_id': str(request.user.id),
			},
		)

		Payment.objects.update_or_create(
			order_id=str(order.id),
			payment_method='stripe',
			defaults={
				'amount': order.total_price,
				'status': 'pending',
				'transaction_id': session.id,
			},
		)

		return Response(
			{
				'checkout_url': session.url,
				'session_id': session.id,
				'order_id': str(order.id),
			},
			status=status.HTTP_200_OK,
		)


def _mark_stripe_payment_paid(order_id, session_id, payment_intent=None):
	payment = Payment.objects.filter(transaction_id=session_id).first()
	if not payment and order_id:
		payment = Payment.objects.filter(order_id=str(order_id), payment_method='stripe').order_by('-created_at').first()

	if payment:
		payment.status = 'paid'
		payment.transaction_id = payment_intent or session_id
		payment.save(update_fields=['status', 'transaction_id'])

	if order_id:
		Order.objects.filter(pk=order_id).update(status='paid')
		try:
			send_order_paid_email.delay(int(order_id))
		except Exception:
			# Payment state should not fail if background email queue is unavailable.
			pass


def _metadata_value(metadata, key):
	if metadata is None:
		return None

	if hasattr(metadata, 'get'):
		value = metadata.get(key)
		if value is not None:
			return value

	try:
		return metadata[key]
	except Exception:
		return None


def _to_mapping(value):
	if value is None:
		return {}

	if isinstance(value, dict):
		return value

	to_dict_recursive = getattr(value, 'to_dict_recursive', None)
	if callable(to_dict_recursive):
		try:
			mapped_value = to_dict_recursive()
			if isinstance(mapped_value, dict):
				return mapped_value
		except Exception:
			pass

	items = getattr(value, 'items', None)
	if callable(items):
		try:
			return dict(items())
		except Exception:
			pass

	return {}


class StripeSuccessView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request):
		if stripe is None:
			return Response({'detail': 'Stripe SDK not installed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		if not settings.STRIPE_SECRET_KEY:
			return Response({'detail': 'STRIPE_SECRET_KEY is not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		session_id = request.query_params.get('session_id')
		if not session_id:
			return Response({'detail': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

		stripe.api_key = settings.STRIPE_SECRET_KEY
		try:
			session = stripe.checkout.Session.retrieve(session_id)
		except Exception:
			return Response({'detail': 'Unable to verify Stripe session.'}, status=status.HTTP_400_BAD_REQUEST)

		payment_status = getattr(session, 'payment_status', None)
		if payment_status != 'paid':
			return Response({'detail': 'Payment is not completed yet.'}, status=status.HTTP_400_BAD_REQUEST)

		metadata = getattr(session, 'metadata', None)
		order_id = _metadata_value(metadata, 'order_id')
		payment_intent = getattr(session, 'payment_intent', None)
		_mark_stripe_payment_paid(order_id, session_id, payment_intent)

		return Response(
			{
				'detail': 'Payment successful.',
				'order_id': order_id,
				'session_id': session_id,
				'payment_status': payment_status,
			},
			status=status.HTTP_200_OK,
		)


class StripeCancelView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request):
		return Response({'detail': 'Payment cancelled.'}, status=status.HTTP_200_OK)


class StripeWebhookView(APIView):
	authentication_classes = []
	permission_classes = [AllowAny]

	def post(self, request):
		if stripe is None:
			return Response({'detail': 'Stripe SDK not installed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		if not settings.STRIPE_SECRET_KEY:
			return Response({'detail': 'STRIPE_SECRET_KEY is not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		payload = request.body
		signature = request.META.get('HTTP_STRIPE_SIGNATURE')
		stripe.api_key = settings.STRIPE_SECRET_KEY

		try:
			if settings.STRIPE_WEBHOOK_SECRET:
				event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
			else:
				event = json.loads(payload.decode('utf-8'))
		except Exception:
			return Response({'detail': 'Invalid Stripe payload.'}, status=status.HTTP_400_BAD_REQUEST)

		event_map = _to_mapping(event)
		event_type = event_map.get('type') or getattr(event, 'type', None)

		event_data = event_map.get('data') or getattr(event, 'data', None)
		event_data_map = _to_mapping(event_data)
		data_object = _to_mapping(event_data_map.get('object'))

		if event_type == 'checkout.session.completed':
			metadata = data_object.get('metadata')
			order_id = _metadata_value(metadata, 'order_id')
			session_id = data_object.get('id')
			payment_intent = data_object.get('payment_intent')
			_mark_stripe_payment_paid(order_id, session_id, payment_intent)

		elif event_type in ['checkout.session.async_payment_failed', 'payment_intent.payment_failed']:
			order_id = _metadata_value(data_object.get('metadata'), 'order_id')
			if order_id:
				Payment.objects.filter(order_id=str(order_id), payment_method='stripe').update(status='failed')

		return Response({'received': True}, status=status.HTTP_200_OK)
