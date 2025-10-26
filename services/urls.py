from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = router.urls
