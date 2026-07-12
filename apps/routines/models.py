from django.conf import settings
from django.db import models
from django.utils import timezone


def default_logged_time():
    return timezone.localtime().time()


class Routine(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="routines",
    )

    name = models.CharField(max_length=100)

    target_minutes = models.PositiveSmallIntegerField(default=30)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def today_log(self):
        return self.logs.filter(date=timezone.localdate()).first()

    def __str__(self):
        return self.name


class RoutineLog(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    date = models.DateField(db_index=True)

    minutes_spent = models.PositiveSmallIntegerField(default=0)

    logged_time = models.TimeField(default=default_logged_time)

    notes = models.CharField(max_length=255, blank=True)

    @property
    def logged_at(self):
        from datetime import datetime

        return timezone.make_aware(datetime.combine(self.date, self.logged_time))

    class Meta:
        ordering = ["-date"]
        unique_together = ("routine", "date")

    def __str__(self):
        return f"{self.routine.name} - {self.date} ({self.minutes_spent}m)"
