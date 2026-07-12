from django.utils import timezone

from .models import LoginSession


def today_seconds(user):
    today = timezone.localdate()

    sessions = LoginSession.objects.filter(user=user, date=today)

    return sum(session.duration_seconds for session in sessions)
