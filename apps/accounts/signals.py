from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LoginSession, Profile, User


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
