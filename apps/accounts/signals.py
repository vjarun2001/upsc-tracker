from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LoginSession, Profile, User
from .services import seconds_until_cutoff


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(user_logged_in)
def start_login_session(sender, request, user, **kwargs):
    now = timezone.now()

    LoginSession.objects.create(
        user=user,
        date=timezone.localdate(),
        login_at=now,
        last_seen_at=now,
    )

    # Force a fresh login (and re-collection of the day's Unslept Hours) every day —
    # the session cookie itself expires at 23:59:59 tonight, not on a rolling window.
    if request is not None:
        request.session.set_expiry(seconds_until_cutoff())


@receiver(user_logged_out)
def close_login_session(sender, request, user, **kwargs):
    if user is None:
        return

    session = (
        LoginSession.objects.filter(user=user, logout_at__isnull=True)
        .order_by("-login_at")
        .first()
    )

    if session:
        session.logout_at = timezone.now()
        session.save(update_fields=["logout_at"])
