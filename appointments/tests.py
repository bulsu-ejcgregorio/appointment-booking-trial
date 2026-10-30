from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Appointment


class AppointmentViewTests(TestCase):
    def setUp(self):
        self.appt = Appointment.objects.create(
            client_name='Ana Reyes',
            email='ana@example.com',
            service=Appointment.Service.CHECKUP,
            scheduled_for=timezone.now(),
        )

    def test_home_lists_appointments(self):
        response = self.client.get(reverse('appointments:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana Reyes')

    def test_detail_shows_appointment(self):
        response = self.client.get(
            reverse('appointments:detail', args=[self.appt.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ana@example.com')

    def test_detail_missing_returns_404(self):
        response = self.client.get(
            reverse('appointments:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)
