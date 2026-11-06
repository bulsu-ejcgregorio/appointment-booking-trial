import re

from django.core.exceptions import ValidationError
from django.db import models


def validate_ph_phone(value):
    """Philippine mobile number: 11 digits starting with 09 (e.g. 09171234567)."""
    cleaned = re.sub(r'[\s-]', '', value)  # allow spaces and dashes when typing
    if not re.fullmatch(r'09\d{9}', cleaned):
        raise ValidationError(
            'Enter a valid mobile number: 11 digits starting with 09 '
            '(e.g. 09171234567).')


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    duration_minutes = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Client(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, validators=[validate_ph_phone])

    def __str__(self):
        return self.full_name


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'{self.client} - {self.service} ({self.scheduled_at:%Y-%m-%d %H:%M})'