from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment, Client, Service


def future_date(days=7):
    """A date safely in the future, in the project's time zone."""
    return timezone.localdate() + timedelta(days=days)


def make_datetime(date, time_str='10:00'):
    """Build an aware datetime from a date and an 'HH:MM' string."""
    hour, minute = map(int, time_str.split(':'))
    naive = timezone.datetime(date.year, date.month, date.day, hour, minute)
    return timezone.make_aware(naive)


class BaseTestCase(TestCase):
    """Shared sample data for all tests."""

    def setUp(self):
        self.service = Service.objects.create(
            name='Consultation', duration_minutes=30)
        self.client_a = Client.objects.create(
            full_name='Client A', email='a@example.com', phone='111')
        self.client_b = Client.objects.create(
            full_name='Client B', email='b@example.com', phone='222')

    def make_appointment(self, client=None, time_str='10:00', days=7, **extra):
        return Appointment.objects.create(
            client=client or self.client_a,
            service=self.service,
            scheduled_at=make_datetime(future_date(days), time_str),
            **extra,
        )

    def form_data(self, client=None, time_str='10:00', days=7,
                  status='scheduled'):
        return {
            'client': (client or self.client_a).pk,
            'service': self.service.pk,
            'date': future_date(days).isoformat(),
            'time': time_str,
            'status': status,
            'notes': '',
        }


class ModelTests(BaseTestCase):
    def test_str_methods(self):
        self.assertEqual(str(self.service), 'Consultation')
        self.assertEqual(str(self.client_a), 'Client A')
        self.assertIn('Client A', str(self.make_appointment()))

    def test_default_status_and_archive_fields(self):
        appointment = self.make_appointment()
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)
        self.assertFalse(appointment.is_archived)
        self.assertIsNone(appointment.archived_at)

    def test_ordering_by_scheduled_at(self):
        later = self.make_appointment(days=9)
        earlier = self.make_appointment(days=8)
        self.assertEqual(list(Appointment.objects.all()), [earlier, later])


class FormValidationTests(BaseTestCase):
    def test_valid_form(self):
        form = AppointmentForm(data=self.form_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_past_date_rejected(self):
        form = AppointmentForm(data=self.form_data(days=-1))
        self.assertFalse(form.is_valid())

    def test_non_30_minute_time_rejected(self):
        form = AppointmentForm(data=self.form_data(time_str='10:15'))
        self.assertFalse(form.is_valid())

    def test_conflict_rejected_on_create(self):
        self.make_appointment()
        form = AppointmentForm(data=self.form_data(client=self.client_b))
        self.assertFalse(form.is_valid())

    def test_conflict_rejected_on_update(self):
        self.make_appointment(time_str='10:00')
        other = self.make_appointment(time_str='11:00')
        form = AppointmentForm(
            data=self.form_data(time_str='10:00'), instance=other)
        self.assertFalse(form.is_valid())

    def test_editing_does_not_conflict_with_itself(self):
        appointment = self.make_appointment()
        form = AppointmentForm(
            data=self.form_data(), instance=appointment)
        self.assertTrue(form.is_valid(), form.errors)

    def test_archived_appointment_does_not_block_slot(self):
        self.make_appointment(
            is_archived=True, archived_at=timezone.now())
        form = AppointmentForm(data=self.form_data(client=self.client_b))
        self.assertTrue(form.is_valid(), form.errors)


class ViewTests(BaseTestCase):
    def test_list_hides_archived(self):
        visible = self.make_appointment(time_str='10:00')
        self.make_appointment(
            client=self.client_b, time_str='11:00',
            is_archived=True, archived_at=timezone.now())
        response = self.client.get(reverse('appointments:appointment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['appointments']), [visible])

    def test_detail_page(self):
        appointment = self.make_appointment()
        response = self.client.get(
            reverse('appointments:appointment_detail', args=[appointment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Client A')

    def test_detail_unknown_id_returns_404(self):
        response = self.client.get(
            reverse('appointments:appointment_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_archived_returns_404(self):
        appointment = self.make_appointment(
            is_archived=True, archived_at=timezone.now())
        response = self.client.get(
            reverse('appointments:appointment_detail', args=[appointment.pk]))
        self.assertEqual(response.status_code, 404)

    def test_create_saves_and_redirects_to_detail(self):
        response = self.client.post(
            reverse('appointments:appointment_create'), self.form_data())
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.get()
        self.assertRedirects(
            response,
            reverse('appointments:appointment_detail', args=[appointment.pk]))

    def test_invalid_create_does_not_save(self):
        response = self.client.post(
            reverse('appointments:appointment_create'),
            self.form_data(days=-1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_update_keeps_record_and_saves_changes(self):
        appointment = self.make_appointment()
        data = self.form_data()
        data['notes'] = 'Updated note'
        data['status'] = 'completed'
        self.client.post(
            reverse('appointments:appointment_update', args=[appointment.pk]),
            data)
        appointment.refresh_from_db()
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(appointment.notes, 'Updated note')
        self.assertEqual(appointment.status, 'completed')


class ArchiveTests(BaseTestCase):
    def test_get_shows_confirmation_and_does_not_archive(self):
        appointment = self.make_appointment()
        response = self.client.get(
            reverse('appointments:appointment_delete', args=[appointment.pk]))
        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertFalse(appointment.is_archived)

    def test_post_archives_without_deleting_row(self):
        appointment = self.make_appointment()
        response = self.client.post(
            reverse('appointments:appointment_delete', args=[appointment.pk]))
        self.assertRedirects(
            response, reverse('appointments:appointment_list'))
        appointment.refresh_from_db()  # row still exists
        self.assertTrue(appointment.is_archived)
        self.assertIsNotNone(appointment.archived_at)
        self.assertEqual(Appointment.objects.count(), 1)

        class SearchFilterTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.appt_a = self.make_appointment(self.client_a, '10:00')
        self.appt_b = self.make_appointment(
            self.client_b, '11:00', status='cancelled')
        self.archived = self.make_appointment(
            self.client_a, '12:00', is_archived=True,
            archived_at=timezone.now())
        self.url = reverse('appointments:appointment_list')

    def listed(self, query=''):
        response = self.client.get(self.url + query)
        self.assertEqual(response.status_code, 200)
        return response, list(response.context['appointments'])

    def test_default_hides_archived(self):
        _, results = self.listed()
        self.assertEqual(results, [self.appt_a, self.appt_b])

    def test_search_by_client_name(self):
        _, results = self.listed('?q=Client B')
        self.assertEqual(results, [self.appt_b])

    def test_search_is_case_insensitive(self):
        _, results = self.listed('?q=client b')
        self.assertEqual(results, [self.appt_b])

    def test_filter_by_status(self):
        _, results = self.listed('?status=cancelled')
        self.assertEqual(results, [self.appt_b])

    def test_include_archived(self):
        _, results = self.listed('?archived=1')
        self.assertEqual(results, [self.appt_a, self.appt_b, self.archived])

    def test_empty_results_message(self):
        response, results = self.listed('?q=zzz')
        self.assertEqual(results, [])
        self.assertContains(response, 'No appointments match your search')