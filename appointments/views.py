from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, Availability
from .serializers import AppointmentSerializer, AvailabilitySerializer
from .permissions import IsCustomerOrReadOnly

class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Availability.objects.none()  # hide provider availabilities to anonymous
        if user.role == 'provider':
            return Availability.objects.filter(provider=user)
        if user.role == 'admin':
            return Availability.objects.all()
        # customers can only view provider availability via service listing endpoint (not this)
        return Availability.objects.none()


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsCustomerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.all()
        if user.is_anonymous:
            return qs.none()
        if user.role == 'customer':
            return qs.filter(customer=user)
        if user.role == 'provider':
            return qs.filter(provider=user)
        # admin:
        return qs

    def perform_create(self, serializer):
        # serializer will assign provider/customer and end_datetime
        serializer.save()

    @action(detail=True, methods=['post'], url_path='reschedule')
    def reschedule(self, request, pk=None):
        """
        Customer can request reschedule (update start_datetime).
        Enforce time limits: can't reschedule within 24 hours of appointment.
        """
        appointment = self.get_object()
        user = request.user
        if user != appointment.customer and user.role != 'admin':
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        # check time limit: e.g., require reschedule > 24 hours before start
        min_hours = 24
        if appointment.start_datetime - timezone.now() < timedelta(hours=min_hours) and user.role != 'admin':
            return Response({'detail': f'Cannot reschedule within {min_hours} hours of the appointment.'}, status=status.HTTP_400_BAD_REQUEST)

        new_start = request.data.get('start_datetime')
        if not new_start:
            return Response({'detail': 'start_datetime is required'}, status=status.HTTP_400_BAD_REQUEST)

        data = {'start_datetime': new_start, 'service': appointment.service.id}
        serializer = self.get_serializer(instance=appointment, data=data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(status='pending')  # reschedule might re-trigger approval
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        user = request.user
        # Only customer, provider (for their own), or admin
        if not (user == appointment.customer or user == appointment.provider or user.role == 'admin'):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        # enforce cancellation window, e.g., cannot cancel within 2 hours of start (unless admin)
        min_hours_cancel = 2
        if appointment.start_datetime - timezone.now() < timedelta(hours=min_hours_cancel) and user.role != 'admin':
            return Response({'detail': f'Cannot cancel within {min_hours_cancel} hours of the appointment.'}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = 'cancelled'
        appointment.reason = request.data.get('reason', '')
        appointment.save()
        return Response({'detail': 'Appointment cancelled.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='status')
    def change_status(self, request, pk=None):
        """
        Provider or admin can change status to confirmed/rejected/completed.
        """
        appointment = self.get_object()
        user = request.user
        if not (user.role == 'provider' and user == appointment.provider) and user.role != 'admin':
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in ['confirmed', 'rejected', 'completed']:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = new_status
        appointment.save()
        return Response({'detail': f'Status set to {new_status}.'}, status=status.HTTP_200_OK)
