from django.contrib import admin

from .models import DailyTask, PomodoroSession


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "date", "subject", "is_completed")
    list_filter = ("date", "is_completed")


@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_type",
        "user",
        "task",
        "subject",
        "planned_duration_minutes",
        "actual_duration_seconds",
        "is_completed",
        "started_at",
    )
    list_filter = ("session_type", "is_completed")
