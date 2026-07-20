import uuid
from datetime import timedelta

from django.conf import settings as django_settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager

STALE_SESSION_THRESHOLD = timedelta(minutes=5)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    full_name = models.CharField(
        max_length=150,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    is_email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    last_login = models.DateTimeField(
        null=True,
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"
        ordering = ["email"]

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
    )

    timezone = models.CharField(
        max_length=64,
        default="Asia/Kolkata",
    )

    bio = models.TextField(
        blank=True,
    )

    daily_study_target_minutes = models.PositiveIntegerField(default=240)

    def __str__(self):
        return self.user.email


class LoginSession(models.Model):
    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_sessions",
    )

    date = models.DateField(db_index=True)

    login_at = models.DateTimeField()

    last_seen_at = models.DateTimeField()

    logout_at = models.DateTimeField(null=True, blank=True)

    quote_shown = models.BooleanField(default=False)

    class Meta:
        ordering = ["-login_at"]

    @property
    def duration_seconds(self):
        if self.logout_at:
            end = self.logout_at
        else:
            now = timezone.now()
            if now - self.last_seen_at > STALE_SESSION_THRESHOLD:
                end = self.last_seen_at
            else:
                end = now

        return max(0, int((end - self.login_at).total_seconds()))

    def __str__(self):
        return f"{self.user} - {self.date}"