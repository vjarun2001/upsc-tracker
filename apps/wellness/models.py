from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SleepLog(models.Model):
    class Quality(models.TextChoices):
        POOR = "poor", "Poor"
        OKAY = "okay", "Okay"
        GOOD = "good", "Good"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sleep_logs",
    )

    date = models.DateField(db_index=True)

    hours = models.DecimalField(max_digits=4, decimal_places=1)

    quality = models.CharField(
        max_length=10,
        choices=Quality.choices,
        default=Quality.OKAY,
    )

    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user} - {self.date} - {self.hours}h"


class WaterLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="water_logs",
    )

    date = models.DateField(db_index=True)

    glasses = models.PositiveSmallIntegerField(default=0)

    target = models.PositiveSmallIntegerField(default=8)

    class Meta:
        ordering = ["-date"]
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user} - {self.date} - {self.glasses}/{self.target}"


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )

    name = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def current_streak(self):
        today = timezone.localdate()

        done_dates = list(
            self.logs.filter(is_done=True)
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

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="logs",
    )

    date = models.DateField(db_index=True)

    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]
        unique_together = ("habit", "date")

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class MealLog(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meal_logs",
    )

    date = models.DateField(db_index=True)

    meal_type = models.CharField(max_length=10, choices=MealType.choices)

    eaten = models.BooleanField(default=False)

    eaten_at = models.TimeField(null=True, blank=True)

    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["date", "meal_type"]
        unique_together = ("user", "date", "meal_type")

    def __str__(self):
        return f"{self.user} - {self.date} - {self.get_meal_type_display()}"
