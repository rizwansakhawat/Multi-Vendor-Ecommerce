from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, StripeWebhookView, StripeSuccessView, StripeCancelView

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('stripe/success/', StripeSuccessView.as_view(), name='stripe-success'),
    path('stripe/cancel/', StripeCancelView.as_view(), name='stripe-cancel'),
    path('', include(router.urls)),
]
