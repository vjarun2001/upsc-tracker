from django.shortcuts import redirect
from django.urls import reverse

from .services import hours_collected_today

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

        return not hours_collected_today(user)
