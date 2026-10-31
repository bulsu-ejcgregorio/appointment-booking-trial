from datetime import datetime, time, timedelta

from django import forms
from django.utils import timezone

from .models import Appointment


def build_time_choices():
    """30-minute slots from 8:00 AM to 5:30 PM."""
    choices = []
    current = datetime(2000, 1, 1, 8, 0)
    end = datetime(2000, 1, 1, 17, 30)
    while current <= end:
        choices.append((current.strftime('%H:%M'), current.strftime('%I:%M %p')))
        current += timedelta(minutes=30)
    return choices


class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        label='Date',
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    time = forms.ChoiceField(label='Time', choices=build_time_choices)

    class Meta:
        model = Appointment
        fields = ['client', 'service', 'status', 'notes']
        labels = {
            'client': 'Client',
            'service': 'Service',
            'status': 'Status',
            'notes': 'Pet Name and Notes',
        }
        widgets = {
            'notes': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Anything we should know?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Put date and time right after the service field
        self.order_fields(['client', 'service', 'date', 'time', 'status', 'notes'])
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # When editing, fill in the saved date and time
        if self.instance.pk and self.instance.scheduled_at:
            local = timezone.localtime(self.instance.scheduled_at)
            self.initial['date'] = local.date()
            self.initial['time'] = local.strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_str = cleaned_data.get('time')
        status = cleaned_data.get('status')

        if not date or not time_str:
            return cleaned_data

        hour, minute = map(int, time_str.split(':'))
        scheduled_at = timezone.make_aware(
            datetime.combine(date, time(hour, minute)))

        if scheduled_at < timezone.now():
            raise forms.ValidationError('The appointment cannot be in the past.')

        if status == Appointment.Status.SCHEDULED:
            conflicts = Appointment.objects.filter(
                scheduled_at=scheduled_at,
                status=Appointment.Status.SCHEDULED,
                is_archived=False,
            ).exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise forms.ValidationError(
                    'That time slot is already taken by another appointment.')

        cleaned_data['scheduled_at'] = scheduled_at
        return cleaned_data

    def save(self, commit=True):
        self.instance.scheduled_at = self.cleaned_data['scheduled_at']
        return super().save(commit=commit)