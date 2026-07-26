from django.conf import settings
from django.db import models
from django.db.models import Q


class Activity(models.Model):
    class Kind(models.TextChoices):
        STUDY = "study", "Study"
        TUITION = "tuition", "Tuition"
        BREAK = "break", "Break"
        OTHERS = "others", "Others"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )

    name = models.CharField(max_length=100)

    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.CUSTOM)

    color = models.CharField(max_length=20, default="#0d6efd")

    icon = models.CharField(max_length=50, default="bi-bookmark")

    is_active = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class DailyTimer(models.Model):
    class Status(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Running"
        PAUSED = "paused", "Paused"
        ON_BREAK = "on_break", "On Break"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_timers",
    )

    date = models.DateField(db_index=True)

    goal_minutes = models.PositiveIntegerField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.IDLE,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}"


class TimerSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="timer_sessions",
    )

    daily_timer = models.ForeignKey(
        DailyTimer,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    activity = models.ForeignKey(
        Activity,
        on_delete=models.PROTECT,
        related_name="sessions",
    )

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timer_sessions",
    )

    topic = models.ForeignKey(
        "study.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timer_sessions",
    )

    start_at = models.DateTimeField()

    end_at = models.DateTimeField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(default=0)

    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["user", "start_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["daily_timer"],
                condition=Q(end_at__isnull=True),
                name="one_open_timersession_per_daily_timer",
            ),
        ]

    def __str__(self):
        return f"{self.activity.name} ({self.start_at})"


class BreakSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="break_sessions",
    )

    daily_timer = models.ForeignKey(
        DailyTimer,
        on_delete=models.CASCADE,
        related_name="breaks",
    )

    start_at = models.DateTimeField()

    end_at = models.DateTimeField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(default=0)

    reason = models.CharField(max_length=100, blank=True)

    planned_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-start_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["daily_timer"],
                condition=Q(end_at__isnull=True),
                name="one_open_break_per_daily_timer",
            ),
        ]

    def __str__(self):
        return f"Break ({self.start_at})"


class WasteSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="waste_sessions",
    )

    daily_timer = models.ForeignKey(
        DailyTimer,
        on_delete=models.CASCADE,
        related_name="wastes",
    )

    start_at = models.DateTimeField()

    end_at = models.DateTimeField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(default=0)

    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-start_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["daily_timer"],
                condition=Q(end_at__isnull=True),
                name="one_open_waste_per_daily_timer",
            ),
        ]

    def __str__(self):
        return f"Waste ({self.start_at})"


class DailySummary(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_summaries",
    )

    date = models.DateField(db_index=True)

    goal_minutes = models.PositiveIntegerField()

    completed_minutes = models.PositiveIntegerField(default=0)

    missed_minutes = models.PositiveIntegerField(default=0)

    break_minutes = models.PositiveIntegerField(default=0)

    waste_minutes = models.PositiveIntegerField(default=0)

    completion_percent = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    @property
    def status(self):
        if self.completed_minutes == 0:
            return "no_activity"
        return "goal_met" if self.completed_minutes >= self.goal_minutes else "goal_missed"

    def __str__(self):
        return f"{self.user} - {self.date} summary"


class TimerEvent(models.Model):
    class EventType(models.TextChoices):
        DAY_STARTED = "day_started", "Day Started"
        SESSION_STARTED = "session_started", "Session Started"
        SESSION_ENDED = "session_ended", "Session Ended"
        BREAK_STARTED = "break_started", "Break Started"
        BREAK_ENDED = "break_ended", "Break Ended"
        WASTE_STARTED = "waste_started", "Waste Started"
        WASTE_ENDED = "waste_ended", "Waste Ended"
        DAY_CLOSED = "day_closed", "Day Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="timer_events",
    )

    daily_timer = models.ForeignKey(
        DailyTimer,
        on_delete=models.CASCADE,
        related_name="events",
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )

    occurred_at = models.DateTimeField(db_index=True)

    activity = models.ForeignKey(
        Activity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    topic = models.ForeignKey(
        "study.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["occurred_at"]
        indexes = [
            models.Index(fields=["user", "daily_timer", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} @ {self.occurred_at}"
