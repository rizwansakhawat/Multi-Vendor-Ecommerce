from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'product',
            'user',
            'user_email',
            'user_name',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        product = attrs.get('product')

        if self.instance:
            product = product or self.instance.product

        if request and request.user.is_authenticated and product:
            existing = Review.objects.filter(user=request.user, product=product)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError('You have already reviewed this product.')

        return attrs
