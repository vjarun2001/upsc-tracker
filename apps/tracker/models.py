from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_logged_time():
    return timezone.localtime().time()


class Tracker(models.Model):
    class Kind(models.TextChoices):
        BOOLEAN = "boolean", "Yes / No"
        DURATION = "duration", "Duration (minutes)"
        COUNT = "count", "Count"

    class Category(models.TextChoices):
        CUSTOM = "custom", "Custom"
        HEALTH = "health", "Health"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trackers",
    )

    name = models.CharField(max_length=100)

    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.BOOLEAN,
    )

    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.CUSTOM,
    )

    target_value = models.PositiveIntegerField(default=1)

    icon = models.CharField(max_length=50, default="bi-check2-circle")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def today_log(self):
        return self.logs.filter(date=timezone.localdate()).first()

    def current_streak(self):
        today = timezone.localdate()

        done_dates = list(
            self.logs.filter(value__gt=0)
            .order_by("-date")
            .values_list("date", flat=True)
        )

        if not done_dates or done_dates[0] not in (today, today - timedelta(days=1)):
            return 0

        streak = 1
        current = done_dates[0]

        for d in done_dates[1:]:
            if current - d == timedelta(days=1):
                streak += 1
                current = d
            else:
                break

        return streak

    def avg_completion_percent(self, days=30):
        today = timezone.localdate()
        start = today - timedelta(days=days - 1)

        done_days = self.logs.filter(date__gte=start, date__lte=today, value__gt=0).count()

        return round(done_days / days * 100)

    def __str__(self):
        return self.name


class TrackerLog(models.Model):
    tracker = models.ForeignKey(
        Tracker,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    date = models.DateField(db_index=True)

    value = models.PositiveIntegerField(default=0)

    logged_time = models.TimeField(default=default_logged_time)

    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("tracker", "date")

    def __str__(self):
        return f"{self.tracker.name} - {self.date} ({self.value})"
