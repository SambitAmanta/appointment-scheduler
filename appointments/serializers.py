from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from django.conf import settings
from .models import Appointment, Availability
from services.models import Service
from django.contrib.auth import get_user_model

User = get_user_model()

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'provider', 'date', 'start_time', 'end_time', 'is_available']
        read_only_fields = ['provider']

    def create(self, validated_data):
        validated_data['provider'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    service_detail = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    provider_name = serializers.CharField(source='provider.username', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'service', 'service_detail', 'provider', 'provider_name', 'customer', 'customer_name',
            'start_datetime', 'end_datetime', 'status', 'notes', 'created_at', 'updated_at', 'reason'
        ]
        read_only_fields = ['provider', 'customer', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate:
        - service exists
        - computed end_datetime matches service.duration (or allow client to send end_datetime; we recompute)
        - overlapping appointments (respecting buffer)
        - within availability (not blocked)
        """
        request = self.context['request']
        user = request.user

        # Service must exist
        service = data.get('service') or (self.instance.service if self.instance else None)
        if not service:
            raise serializers.ValidationError("Service is required.")

        # compute start and end
        start_dt = data.get('start_datetime') or (self.instance.start_datetime if self.instance else None)
        if not start_dt:
            raise serializers.ValidationError("start_datetime is required.")

        # Compute end from service.duration
        end_dt = start_dt + timedelta(minutes=service.duration)

        # If user is creating: set customer/provider
        provider = service.provider
        customer = user

        # For updates (reschedule by customer or admin), instance might exist:
        # set candidate values
        candidate_start = start_dt
        candidate_end = end_dt

        # Prevent booking in the past
        if candidate_start < timezone.now():
            raise serializers.ValidationError("Cannot book an appointment in the past.")

        # Check provider availability: there must be at least one Availability with is_available=True
        availabilities = Availability.objects.filter(provider=provider, date=candidate_start.date(), is_available=True)
        in_avail = False
        for a in availabilities:
            # convert times to datetimes for comparison
            start_time_dt = timezone.make_aware(timezone.datetime.combine(a.date, a.start_time))
            end_time_dt = timezone.make_aware(timezone.datetime.combine(a.date, a.end_time))
            if candidate_start >= start_time_dt and candidate_end <= end_time_dt:
                in_avail = True
                break
        if not in_avail:
            # if provider has no explicit availability entries for that date consider denial:
            # to be strict, we deny if no matching availability slot found
            raise serializers.ValidationError("Selected time not within provider availability (or provider has blocked the slot).")

        # Overlap check against other appointments for provider (exclude self when updating)
        # consider buffer: use max buffer between existing service and current service
        qs = Appointment.objects.filter(provider=provider).exclude(status='cancelled')
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        for other in qs:
            other_start = other.start_datetime
            other_end = other.end_datetime
            # compute buffer in minutes: take the buffer of either service (conservative)
            other_buffer = getattr(other.service, 'buffer_time', 0) or 0
            this_buffer = getattr(service, 'buffer_time', 0) or 0
            buffer_minutes = max(other_buffer, this_buffer)

            # extended window = other_end + buffer
            other_end_with_buffer = other_end + timedelta(minutes=buffer_minutes)
            candidate_end_with_buffer = candidate_end + timedelta(minutes=buffer_minutes)

            # overlapping if candidate_start < other_end_with_buffer and candidate_end_with_buffer > other_start
            if (candidate_start < other_end_with_buffer) and (candidate_end_with_buffer > other_start):
                raise serializers.ValidationError("This time collides with another appointment for the provider (respecting buffer times).")

        # if all validations pass, store computed times back into data
        data['end_datetime'] = candidate_end
        data['provider'] = provider
        data['customer'] = customer

        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['status'] = 'pending'  # default new booking status
        appointment = super().create(validated_data)
        # (Optional) send notifications / emails here
        return appointment

    @transaction.atomic
    def update(self, instance, validated_data):
        # only certain fields allowed to update depending on user/role; view should check permissions
        return super().update(instance, validated_data)
