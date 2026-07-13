from django.conf import settings
from django.db import models

from apps.common.choices import Phase


class MockTest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mock_tests",
    )

    subject = models.ForeignKey(
        "study.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mock_tests",
    )

    phase = models.CharField(
        max_length=10,
        choices=Phase.choices,
        default=Phase.PRELIMS,
    )

    name = models.CharField(max_length=200)

    test_date = models.DateField()

    total_questions = models.PositiveSmallIntegerField()

    correct = models.PositiveSmallIntegerField()

    incorrect = models.PositiveSmallIntegerField()

    marks_per_correct = models.DecimalField(max_digits=4, decimal_places=2, default=2)

    negative_marks_per_incorrect = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.66
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-test_date"]

    @property
    def unattempted(self):
        return self.total_questions - self.correct - self.incorrect

    @property
    def obtained_marks(self):
        return (self.correct * self.marks_per_correct) - (
            self.incorrect * self.negative_marks_per_incorrect
        )

    @property
    def attempted(self):
        return self.correct + self.incorrect

    @property
    def accuracy_percent(self):
        if not self.attempted:
            return 0
        return round(self.correct / self.attempted * 100, 1)

    def __str__(self):
        return self.name


class TestGoal(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_goal",
    )

    target_score = models.PositiveSmallIntegerField(default=100)

    target_accuracy = models.PositiveSmallIntegerField(default=70)

    next_test_date = models.DateField(null=True, blank=True)

    next_test_name = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Test goal for {self.user}"
