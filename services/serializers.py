from rest_framework import serializers
from .models import Service, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ServiceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'provider_name', 'category', 'category_name',
            'name', 'description', 'price', 'duration', 'buffer_time', 'image'
        ]
        read_only_fields = ['provider']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['provider'] = user
        return super().create(validated_data)
