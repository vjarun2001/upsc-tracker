from django.contrib import admin

from .models import Tracker, TrackerLog


@admin.register(Tracker)
class TrackerAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "kind", "target_value", "is_active")


@admin.register(TrackerLog)
class TrackerLogAdmin(admin.ModelAdmin):
    list_display = ("tracker", "date", "value", "logged_time")
