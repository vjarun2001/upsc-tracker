from datetime import timedelta

from django.urls import reverse
from django.utils import timezone


def get_notifications(user):
    from apps.goals.models import Goal
    from apps.revision.models import RevisionSchedule

    today = timezone.localdate()
    notifications = []

    due_revisions = RevisionSchedule.objects.filter(
        user=user,
        is_done=False,
        scheduled_date__lte=today,
    ).select_related("topic")

    for item in due_revisions:
        notifications.append(
            {
                "message": f"Revise: {item.topic.title}",
                "url": reverse("revision:today"),
                "icon": "bi-arrow-repeat",
            }
        )

    due_soon_goals = Goal.objects.filter(
        user=user,
        is_completed=False,
        target_date__isnull=False,
        target_date__lte=today + timedelta(days=3),
    )

    for goal in due_soon_goals:
        notifications.append(
            {
                "message": f"Goal due soon: {goal.title}",
                "url": reverse("goals:list"),
                "icon": "bi-bullseye",
            }
        )

    return notifications
