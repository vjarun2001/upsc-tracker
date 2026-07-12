from django.conf import settings
from django.db import models


class RevisionSchedule(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revision_schedules",
    )

    topic = models.ForeignKey(
        "study.Topic",
        on_delete=models.CASCADE,
        related_name="revision_schedules",
    )

    stage_days = models.PositiveSmallIntegerField(
        help_text="How many days after completion this revision falls due."
    )

    scheduled_date = models.DateField(db_index=True)

    is_done = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_date"]

    def __str__(self):
        return f"{self.topic.title} (+{self.stage_days}d)"
