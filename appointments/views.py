from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment


def appointment_list(request):
    """List appointments, with optional search by client name and status filter."""
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    include_archived = request.GET.get('archived') == '1'

    appointments = Appointment.objects.select_related('client', 'service')
    if not include_archived:
        appointments = appointments.filter(is_archived=False)
    if q:
        appointments = appointments.filter(client__full_name__icontains=q)
    if status in Appointment.Status.values:
        appointments = appointments.filter(status=status)

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'q': q,
        'status': status,
        'include_archived': include_archived,
        'status_choices': Appointment.Status.choices,
        'filters_active': bool(q or status or include_archived),
    })


def appointment_detail(request, pk):
    """Show one appointment; archived or unknown ids return 404."""
    appointment = get_object_or_404(
        Appointment.objects.select_related('client', 'service'),
        pk=pk, is_archived=False)
    return render(request, 'appointments/appointment_detail.html',
                  {'appointment': appointment})


def appointment_create(request):
    form = AppointmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appointment = form.save()
        return redirect('appointments:appointment_detail', pk=appointment.pk)
    return render(request, 'appointments/appointment_form.html',
                  {'form': form, 'title': 'New Appointment'})


def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, is_archived=False)
    form = AppointmentForm(request.POST or None, instance=appointment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('appointments:appointment_detail', pk=appointment.pk)
    return render(request, 'appointments/appointment_form.html',
                  {'form': form, 'title': 'Edit appointment',
                   'appointment': appointment})


def appointment_delete(request, pk):
    """GET shows a confirmation page; POST archives (soft delete)."""
    appointment = get_object_or_404(Appointment, pk=pk, is_archived=False)
    if request.method == 'POST':
        appointment.is_archived = True
        appointment.archived_at = timezone.now()
        appointment.save()
        return redirect('appointments:appointment_list')
    return render(request, 'appointments/appointment_confirm_delete.html',
                  {'appointment': appointment})