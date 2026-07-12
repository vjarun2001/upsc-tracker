from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    verb = models.CharField(max_length=100)

    description = models.CharField(max_length=255)

    url = models.CharField(max_length=255, blank=True)

    icon = models.CharField(max_length=50, default="bi-dot")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return self.description
