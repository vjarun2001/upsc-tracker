from django.contrib import admin

from .models import RevisionSchedule


@admin.register(RevisionSchedule)
class RevisionScheduleAdmin(admin.ModelAdmin):
    list_display = ("topic", "user", "stage_days", "scheduled_date", "is_done")
    list_filter = ("is_done", "stage_days")
