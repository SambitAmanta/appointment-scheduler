from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from appointments.models import Appointment
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_booking_notification(appointment_id, event_type):
   try:
     appt = Appointment.objects.select_related('customer', 'provider', 'service').get(id=appointment_id)
   except Appointment.DoesNotExist:
     return

   subject = f"Appointment {event_type.capitalize()}"
   message = (
     f"Hello {appt.customer.username},\n\n"
     f"Your appointment for {appt.service.name} on {appt.start_datetime:%Y-%m-%d %H:%M} has been {event_type}."
   )
   send_mail(subject, message, None, [appt.customer.email])

   # Notify provider too
   if appt.provider.email:
     send_mail(subject, f"Customer {appt.customer.username} has {event_type} an appointment.",
         None, [appt.provider.email])

@shared_task
def daily_reminder():
   tomorrow = timezone.now() + timezone.timedelta(days=1)
   appointments = Appointment.objects.filter(
     start_datetime__date=tomorrow.date(),
     status__in=['confirmed','pending']
   )
   for appt in appointments:
     send_mail(
       'Appointment Reminder',
       f'Reminder: You have {appt.service.name} tomorrow at {appt.start_datetime:%H:%M}',
       None,
       [appt.customer.email],
     )
