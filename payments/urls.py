from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, StripeWebhookView, StripeSuccessView, StripeCancelView

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('stripe/success/', StripeSuccessView.as_view(), name='stripe-success'),
    path('stripe/cancel/', StripeCancelView.as_view(), name='stripe-cancel'),
    path('', include(router.urls)),
]


#####  stripe listen --forward-to http://127.0.0.1:8000/api/payments/stripe/webhook/ 


# # # # docker run -d --name my-redis -p 6379:6379 redis
# # Great! Redis is now running inside Docker. Your "Postman" (Broker) is officially active on port 6379.

# # # # celery -A config worker --loglevel=info

# # # celery -A config worker --loglevel=info --pool=solo --concurrency=1
# celery -A config worker -l INFO

