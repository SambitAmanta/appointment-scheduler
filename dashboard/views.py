from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, F, Q, DateField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.core.cache import cache
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

from appointments.models import Appointment
from services.models import Service
from django.contrib.auth import get_user_model

User = get_user_model()

CACHE_TTL = 60  # seconds; tune as needed or use settings

class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'admin':
            return Response({'detail': 'Forbidden'}, status=403)

        cache_key = f"admin_dashboard_v1"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # basic totals
        total_bookings = Appointment.objects.filter().count()
        total_confirmed = Appointment.objects.filter(status='confirmed').count()
        total_cancelled = Appointment.objects.filter(status='cancelled').count()
        total_revenue = Appointment.objects.filter(status='completed').aggregate(
            revenue=Sum(F('service__price'))
        )['revenue'] or 0

        # top services (by bookings & revenue) - last 90 days
        since = datetime.now() - timedelta(days=90)
        top_services_qs = (Appointment.objects
            .filter(created_at__gte=since, status__in=['confirmed','completed'])
            .values('service')
            .annotate(bookings=Count('id'),
                      revenue=Sum(F('service__price')))
            .order_by('-bookings')[:10])

        # bookings trend (last 30 days)
        last_30 = datetime.now() - timedelta(days=30)
        trend_qs = (Appointment.objects
            .filter(created_at__gte=last_30)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(bookings=Count('id'))
            .order_by('day'))

        # format trend
        trend = [{'date': t['day'].date(), 'bookings': t['bookings']} for t in trend_qs]

        payload = {
            'totals': {
                'total_bookings': total_bookings,
                'total_confirmed': total_confirmed,
                'total_cancelled': total_cancelled,
                'total_revenue': float(total_revenue),
            },
            'top_services': list(top_services_qs),
            'trend': trend,
        }

        cache.set(cache_key, payload, CACHE_TTL)
        return Response(payload)


class ProviderDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ['provider', 'admin']:
            return Response({'detail': 'Forbidden'}, status=403)

        cache_key = f"provider_dashboard_{user.id}_v1"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # totals for provider
        qs = Appointment.objects.filter(provider=user)
        total_bookings = qs.count()
        upcoming = qs.filter(start_datetime__gte=datetime.now(), status__in=['pending','confirmed']).count()
        completed = qs.filter(status='completed').count()
        cancelled = qs.filter(status='cancelled').count()
        revenue = qs.filter(status='completed').aggregate(revenue=Sum(F('service__price')))['revenue'] or 0

        # provider utilization: fraction of booked minutes vs available minutes (over next 7 days)
        # compute booked minutes in next 7 days
        start = datetime.now()
        end = start + timedelta(days=7)
        booked = qs.filter(start_datetime__gte=start, start_datetime__lte=end, status__in=['pending','confirmed','completed'])
        booked_minutes = 0
        for a in booked:
            duration = (a.end_datetime - a.start_datetime).total_seconds() / 60.0
            booked_minutes += duration

        # estimate available minutes by summing provider Availability for next 7 days
        from appointments.models import Availability
        avails = Availability.objects.filter(provider=user, date__gte=start.date(), date__lte=end.date(), is_available=True)
        available_minutes = 0
        for av in avails:
            dt_start = datetime.combine(av.date, av.start_time)
            dt_end = datetime.combine(av.date, av.end_time)
            available_minutes += (dt_end - dt_start).total_seconds() / 60.0

        utilization = (booked_minutes / available_minutes * 100.0) if available_minutes > 0 else None

        # bookings trend for provider (7 days)
        trend_qs = (qs.filter(start_datetime__gte=start, start_datetime__lte=end)
                    .annotate(day=TruncDay('start_datetime'))
                    .values('day')
                    .annotate(bookings=Count('id'))
                    .order_by('day'))
        trend = [{'date': t['day'].date(), 'bookings': t['bookings']} for t in trend_qs]

        payload = {
            'totals': {
                'total_bookings': total_bookings,
                'upcoming': upcoming,
                'completed': completed,
                'cancelled': cancelled,
                'revenue': float(revenue),
                'utilization_percent': utilization
            },
            'trend': trend,
        }
        cache.set(cache_key, payload, CACHE_TTL)
        return Response(payload)


class CustomerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # totals for customer
        qs = Appointment.objects.filter(customer=user)
        upcoming = qs.filter(start_datetime__gte=datetime.now(), status__in=['pending','confirmed']).count()
        past = qs.filter(start_datetime__lt=datetime.now()).count()
        cancelled = qs.filter(status='cancelled').count()

        payload = {
            'totals': {
                'upcoming': upcoming,
                'past': past,
                'cancelled': cancelled,
            }
        }
        return Response(payload)



