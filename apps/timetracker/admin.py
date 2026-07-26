from django.contrib import admin

from .models import (
    Activity,
    BreakSession,
    DailySummary,
    DailyTimer,
    TimerEvent,
    TimerSession,
    WasteSession,
)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "kind", "is_active", "order")
    list_filter = ("kind", "is_active")


@admin.register(DailyTimer)
class DailyTimerAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "status", "goal_minutes", "closed_at")
    list_filter = ("status", "date")


@admin.register(TimerSession)
class TimerSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "start_at", "end_at", "duration_seconds")
    list_filter = ("activity",)


@admin.register(BreakSession)
class BreakSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "start_at", "end_at", "duration_seconds", "planned_minutes", "reason")


@admin.register(WasteSession)
class WasteSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "start_at", "end_at", "duration_seconds", "reason")


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "goal_minutes",
        "completed_minutes",
        "missed_minutes",
        "completion_percent",
    )
    list_filter = ("date",)


@admin.register(TimerEvent)
class TimerEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "occurred_at", "label")
    list_filter = ("event_type",)
