from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "verb", "description", "timestamp")
    list_filter = ("verb",)
