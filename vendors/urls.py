from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payouts', views.VendorPayoutViewSet, basename='vendor-payout')

urlpatterns = [
    path('register/', views.VendorRegistrationView.as_view(), name='vendor-register'),
    path('profile/', views.VendorProfileView.as_view(), name='vendor-profile'),
    path('dashboard/', views.VendorDashboardView.as_view(), name='vendor-dashboard'),
    path('', include(router.urls)),
]