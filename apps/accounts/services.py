from datetime import datetime
from datetime import time as dtime

from django.utils import timezone

from .models import LoginSession


def today_seconds(user):
    today = timezone.localdate()

    sessions = LoginSession.objects.filter(user=user, date=today)

    return sum(session.duration_seconds for session in sessions)


def seconds_until_cutoff():
    """Seconds remaining until 23:59:59 today — the same day-boundary used by
    apps.timetracker.services._rollover_close, kept consistent across the app."""
    now = timezone.localtime()
    cutoff = timezone.make_aware(datetime.combine(now.date(), dtime(23, 59, 59)), now.tzinfo)

    return max(0, int((cutoff - now).total_seconds()))
