from .models import ActivityLog


def log_activity(user, verb, description, url="", icon="bi-dot"):
    return ActivityLog.objects.create(
        user=user,
        verb=verb,
        description=description,
        url=url,
        icon=icon,
    )
