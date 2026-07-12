from django.utils import timezone

from .models import ActivityLog


def log_activity(user, verb, description, url="", icon="bi-dot"):
    return ActivityLog.objects.create(
        user=user,
        verb=verb,
        description=description,
        url=url,
        icon=icon,
    )


def get_today_activity(user):
    today = timezone.localdate()

    return ActivityLog.objects.filter(user=user, timestamp__date=today)
