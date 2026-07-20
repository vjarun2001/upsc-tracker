from django.conf import settings
from django.db import models


class Goal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goals",
    )

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    target_date = models.DateField(null=True, blank=True)

    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["is_completed", "target_date", "-created_at"]

    @property
    def progress_percent(self):
        total = self.milestones.count()
        if not total:
            return 100 if self.is_completed else 0
        done = self.milestones.filter(is_completed=True).count()
        return int(done / total * 100)

    def __str__(self):
        return self.title


class Milestone(models.Model):
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name="milestones",
    )

    title = models.CharField(max_length=200)

    is_completed = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title
