from django.contrib import admin

from .models import RevisionSchedule


@admin.register(RevisionSchedule)
class RevisionScheduleAdmin(admin.ModelAdmin):
    list_display = ("topic", "user", "stage", "scheduled_date", "is_done", "confidence")
    list_filter = ("is_done", "stage", "confidence")
