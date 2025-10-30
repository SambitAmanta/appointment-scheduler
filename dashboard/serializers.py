from rest_framework import serializers

class BookingTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    bookings = serializers.IntegerField()

class TopServiceSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    service_name = serializers.CharField()
    provider_id = serializers.IntegerField()
    provider_name = serializers.CharField()
    bookings = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
