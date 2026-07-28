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


def hours_collected_today(user):
    """Whether this user has already submitted today's Unslept Hours, in ANY
    LoginSession — not just the current one. A session can end early for reasons
    that have nothing to do with a new day starting (browser crash, laptop losing
    power, manually logging out, clearing cookies); re-logging in the same day
    must not re-trigger the prompt just because a fresh LoginSession row exists."""
    return LoginSession.objects.filter(
        user=user, date=timezone.localdate(), hours_collected=True
    ).exists()
