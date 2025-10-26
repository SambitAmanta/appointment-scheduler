from rest_framework import viewsets, permissions, filters
from .models import Service, Category
from .serializers import ServiceSerializer, CategorySerializer
from .permissions import IsAdminOrProvider

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrProvider]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrProvider]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category__name', 'provider__username']
    ordering_fields = ['price', 'duration']

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Service.objects.all()
        if user.role == 'provider':
            return Service.objects.filter(provider=user)
        return Service.objects.all()
