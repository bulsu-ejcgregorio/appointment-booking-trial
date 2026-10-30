"""Root URL configuration: the entry point for every request."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Hand everything else to the appointments app's own urls.py
    path('', include('appointments.urls')),
]
