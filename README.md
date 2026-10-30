# Appointment Booking System

IT 401W | Web Programming and Frameworks | Final Course Output

## Overview

Small service providers often track bookings through chat or paper, which makes schedules hard to review and allows double bookings.

This Django web application lets a staff user create, view, edit, cancel and archive client appointments. Service, client, time, status and notes are kept in one schedule. Deleting an appointment **archives** it (soft delete): the row stays in the database with `is_archived` and `archived_at` set.

**Group:** G5 (
    MICHAEL
    KEZIAH
    EARL
    JC
    NINA
    HEHE
)

## Features

- List upcoming (non-archived) appointments in chronological order
- Create an appointment (client, service, date, time, status, notes)
- View the full details of one appointment (unknown or archived ids return 404)
- Update an appointment, including its status
- Archive an appointment after a confirmation page (POST only, with CSRF protection)
- Prevent two scheduled, active appointments from using the same date and time
- Reject dates in the past; times are limited to 30-minute slots
- Django admin for Service, Client and Appointment

## Data model

```
Service (1) ---< Appointment >--- (1) Client
```

| Model | Fields |
|---|---|
| Service | name (unique), duration_minutes, active |
| Client | full_name, email, phone |
| Appointment | client (FK, PROTECT), service (FK, PROTECT), scheduled_at, status, notes, is_archived, archived_at, created_at, updated_at |

Appointments are ordered by `scheduled_at`. List queries use `select_related("client", "service")` and filter `is_archived=False`.

## Pages

| URL | Name | Purpose |
|---|---|---|
| `/` | appointment_list | List appointments |
| `/appointments/new/` | appointment_create | Create form |
| `/appointments/<id>/` | appointment_detail | One appointment |
| `/appointments/<id>/edit/` | appointment_update | Prefilled edit form |
| `/appointments/<id>/delete/` | appointment_delete | Confirm on GET, archive on POST |
| `/admin/` | | Django admin |

## How to run

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ for the admin. In the admin, add at least one **Service** and one **Client** before booking an appointment.

## Demo script

1. Log in to `/admin/` and show the Service, Client and Appointment models.
2. On the site, click **+ New appointment** and book one. Show the detail page with the status label.
3. Try to book the same date and time again and show the "slot already taken" error.
4. Try a past date and show the error.
5. Click **Edit**, change the notes or status, save, and show the updated detail page.
6. Click **Archive**, show the confirmation page, then confirm. The appointment disappears from the list.
7. Open `/admin/` and show the archived row still exists with `is_archived` checked and `archived_at` filled in.
8. Open the archived appointment's URL to show the 404.
9. Book the archived appointment's old time slot again to show archived rows do not block bookings.

## Security and validation

- `{% csrf_token %}` and `method="post"` on every create, update and archive form
- `form.is_valid()` is called before `form.save()`
- Redirect after every successful POST
- Validation: no past dates, 30-minute slots only, no double booking (an appointment never conflicts with itself when editing)
