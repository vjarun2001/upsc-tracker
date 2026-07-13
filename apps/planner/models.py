from django.conf import settings
from django.db import models

from apps.common.choices import Phase


class DailyTask(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_tasks",
    )

    date = models.DateField(db_index=True)

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_tasks",
    )

    tracker = models.ForeignKey(
        "tracker.Tracker",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_tasks",
    )

    title = models.CharField(max_length=200)

    notes = models.TextField(blank=True)

    start_time = models.TimeField(null=True, blank=True)

    end_time = models.TimeField(null=True, blank=True)

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    phase = models.CharField(
        max_length=10,
        choices=Phase.choices,
        blank=True,
    )

    is_completed = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "order", "created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self):
        return self.title


class PomodoroSession(models.Model):
    class SessionType(models.TextChoices):
        FOCUS = "focus", "Focus"
        SHORT_BREAK = "short_break", "Short Break"
        LONG_BREAK = "long_break", "Long Break"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pomodoro_sessions",
    )

    task = models.ForeignKey(
        DailyTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pomodoro_sessions",
    )

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pomodoro_sessions",
    )

    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.FOCUS,
    )

    planned_duration_minutes = models.PositiveSmallIntegerField(default=25)

    actual_duration_seconds = models.PositiveIntegerField(default=0)

    is_completed = models.BooleanField(default=False)

    started_at = models.DateTimeField()

    completed_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.get_session_type_display()} ({self.actual_duration_seconds}s)"
