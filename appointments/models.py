from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from services.models import Service

User = settings.AUTH_USER_MODEL

class Availability(models.Model):
    """
    Provider availability / blocked slots for a particular date.
    Use `is_available=False` for blocked slots (breaks/holidays).
    """
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)  # False = blocked

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('provider', 'date', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.provider.username} - {self.date} {self.start_time}-{self.end_time} ({'open' if self.is_available else 'blocked'})"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_provider')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_customer')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # optionally store a cancellation/reschedule reason
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_datetime']

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("start_datetime must be before end_datetime")
        if self.provider == self.customer:
            raise ValidationError("Provider and customer cannot be the same user.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} ({self.customer.username}) @ {self.start_datetime} -> {self.status}"
