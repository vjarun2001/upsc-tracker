from django.conf import settings
from django.db import models


class Quote(models.Model):
    text = models.CharField(max_length=300)

    author = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:50]


class ExamProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_profile",
    )

    prelims_date = models.DateField(null=True, blank=True)

    mains_date = models.DateField(null=True, blank=True)

    interview_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Exam profile for {self.user}"
