from django.shortcuts import redirect
from django.urls import reverse

from .models import LoginSession

EXEMPT_PREFIXES = (
    "/accounts/",
    "/static/",
    "/media/",
    "/admin/",
    "/sw.js",
)


class DailyCheckInMiddleware:
    """Redirects to the daily Unslept Hours prompt until it's been filled in for
    the current login — everything else in the app waits behind this each day."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._needs_daily_hours(request):
            return redirect(reverse("accounts:daily_hours"))

        return self.get_response(request)

    def _needs_daily_hours(self, request):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated or user.is_staff:
            return False

        if request.path.startswith(EXEMPT_PREFIXES):
            return False

        session = (
            LoginSession.objects.filter(user=user, logout_at__isnull=True)
            .order_by("-login_at")
            .first()
        )

        return bool(session and not session.hours_collected)
