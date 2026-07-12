from django.db import models
from django.conf import settings


class Subject(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subjects"
    )

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#007bff")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    title = models.CharField(max_length=200)

    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class StudySession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]

    @property
    def duration_minutes(self):
        return int(
            (self.end_time - self.start_time).total_seconds() / 60
        )

    def __str__(self):
        return f"{self.subject.name}"