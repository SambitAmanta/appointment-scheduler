from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from appointments.models import Appointment
from notifications.tasks import send_booking_notification

@receiver(post_save, sender=Appointment)
def appointment_saved(sender, instance, created, **kwargs):
   if created:
     event = 'booked'
   elif instance.status == 'cancelled':
     event = 'cancelled'
   else:
     event = 'updated'
   send_booking_notification.delay(instance.id, event)

@receiver(pre_delete, sender=Appointment)
def appointment_deleted(sender, instance, **kwargs):
   send_booking_notification.delay(instance.id, 'deleted')
