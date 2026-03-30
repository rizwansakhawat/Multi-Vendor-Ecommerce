from rest_framework import serializers

from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = [
			'id',
			'order_id',
			'amount',
			'payment_method',
			'status',
			'transaction_id',
			'created_at',
		]
		read_only_fields = ['id', 'created_at']

	def validate_order_id(self, value):
		if not str(value).strip():
			raise serializers.ValidationError('order_id is required.')
		return str(value)

	def validate_status(self, value):
		allowed_statuses = {'pending', 'paid', 'failed', 'refunded'}
		if value.lower() not in allowed_statuses:
			raise serializers.ValidationError(
				'status must be one of: pending, paid, failed, refunded.'
			)
		return value.lower()

