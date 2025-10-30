from django.urls import path
from .views import AdminDashboardAPIView, ProviderDashboardAPIView, CustomerDashboardAPIView, DashboardExportAPIView

urlpatterns = [
    path('admin/', AdminDashboardAPIView.as_view(), name='dashboard-admin'),
    path('provider/', ProviderDashboardAPIView.as_view(), name='dashboard-provider'),
    path('customer/', CustomerDashboardAPIView.as_view(), name='dashboard-customer'),
]
