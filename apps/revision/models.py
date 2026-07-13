from django.conf import settings
from django.db import models


class RevisionSchedule(models.Model):
    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

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

    stage = models.PositiveSmallIntegerField(
        default=1,
        help_text="Revision round: R1 through R5.",
    )

    scheduled_date = models.DateField(db_index=True)

    is_done = models.BooleanField(default=False)

    confidence = models.CharField(
        max_length=10,
        choices=Confidence.choices,
        blank=True,
    )

    done_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_date"]
        unique_together = ("topic", "stage")

    def __str__(self):
        return f"{self.topic.title} (R{self.stage})"
