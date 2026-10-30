from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment


def appointment_list(request):
    """List upcoming (non-archived) appointments, ordered by date."""
    appointments = (
        Appointment.objects.filter(is_archived=False)
        .select_related('client', 'service')
    )
    return render(request, 'appointments/appointment_list.html',
                  {'appointments': appointments})


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
                  {'form': form, 'title': 'New appointment'})


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