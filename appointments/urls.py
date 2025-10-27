from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AvailabilityViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointments')
router.register(r'availability', AvailabilityViewSet, basename='availability')

urlpatterns = router.urls
