from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.goals.models import Goal
from apps.mocktest.models import MockTest
from apps.notes.models import Note
from apps.planner.models import DailyTask
from apps.study.models import StudySession

from .services import log_activity


@receiver(post_save, sender=StudySession)
def on_study_session_created(sender, instance, created, **kwargs):
    if created:
        log_activity(
            instance.user,
            "study_session",
            f"Logged a study session on {instance.subject.name} ({instance.duration_minutes} min)",
            url="/study/",
            icon="bi-book",
        )


@receiver(post_save, sender=Note)
def on_note_created(sender, instance, created, **kwargs):
    if created:
        log_activity(
            instance.user,
            "note",
            f"Wrote a note: {instance.title}",
            url="/notes/",
            icon="bi-journal-text",
        )


@receiver(post_save, sender=MockTest)
def on_mock_test_created(sender, instance, created, **kwargs):
    if created:
        log_activity(
            instance.user,
            "mock_test",
            f"Logged mock test: {instance.name} ({instance.obtained_marks} marks)",
            url="/mocktest/",
            icon="bi-clipboard-data",
        )


@receiver(post_save, sender=DailyTask)
def on_daily_task_created(sender, instance, created, **kwargs):
    if created:
        log_activity(
            instance.user,
            "task_added",
            f"Added task: {instance.title}",
            url="/planner/",
            icon="bi-list-check",
        )


@receiver(post_save, sender=Goal)
def on_goal_created(sender, instance, created, **kwargs):
    if created:
        log_activity(
            instance.user,
            "goal_added",
            f"Set a new goal: {instance.title}",
            url="/goals/",
            icon="bi-bullseye",
        )


