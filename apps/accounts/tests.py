from datetime import datetime
from datetime import time as dtime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import DailyUnsleptHoursForm
from .models import LoginSession
from .services import seconds_until_cutoff

User = get_user_model()


class SecondsUntilCutoffTests(TestCase):
    def test_computes_seconds_to_23_59_59_today(self):
        now = timezone.make_aware(datetime.combine(timezone.localdate(), dtime(22, 0, 0)))
        with mock.patch("apps.accounts.services.timezone.localtime", return_value=now):
            self.assertEqual(seconds_until_cutoff(), 1 * 3600 + 59 * 60 + 59)

    def test_zero_when_past_cutoff(self):
        now = timezone.make_aware(datetime.combine(timezone.localdate(), dtime(23, 59, 59, 500000)))
        with mock.patch("apps.accounts.services.timezone.localtime", return_value=now):
            self.assertEqual(seconds_until_cutoff(), 0)


class DailyUnsleptHoursFormTests(TestCase):
    def test_rejects_hours_beyond_remaining_day(self):
        now = timezone.make_aware(datetime.combine(timezone.localdate(), dtime(22, 0, 0)))
        with mock.patch("apps.accounts.forms.seconds_until_cutoff", return_value=int((timezone.make_aware(
            datetime.combine(timezone.localdate(), dtime(23, 59, 59))
        ) - now).total_seconds())):
            form = DailyUnsleptHoursForm(data={"hours": 5})
            self.assertFalse(form.is_valid())
            self.assertIn("Only 1h left today", form.errors["hours"][0])

    def test_accepts_hours_within_remaining_day(self):
        with mock.patch("apps.accounts.forms.seconds_until_cutoff", return_value=5 * 3600):
            form = DailyUnsleptHoursForm(data={"hours": 4})
            self.assertTrue(form.is_valid())


class DailyCheckInMiddlewareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="checkin-tester@example.com", password="testpass123")

    def test_uncollected_session_redirects_to_daily_hours(self):
        self.client.login(email="checkin-tester@example.com", password="testpass123")
        response = self.client.get(reverse("analytics:dashboard"))
        self.assertRedirects(response, reverse("accounts:daily_hours"))

    def test_profile_page_exempt_even_when_uncollected(self):
        self.client.login(email="checkin-tester@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

    def test_no_redirect_once_hours_collected(self):
        self.client.login(email="checkin-tester@example.com", password="testpass123")
        LoginSession.objects.filter(user=self.user, logout_at__isnull=True).update(hours_collected=True)

        response = self.client.get(reverse("analytics:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_user_exempt(self):
        staff = User.objects.create_user(email="staff-tester@example.com", password="testpass123", is_staff=True)
        self.client.login(email="staff-tester@example.com", password="testpass123")

        response = self.client.get(reverse("analytics:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_daily_hours_view_saves_and_marks_collected(self):
        self.client.login(email="checkin-tester@example.com", password="testpass123")

        with mock.patch("apps.accounts.forms.seconds_until_cutoff", return_value=23 * 3600):
            response = self.client.post(reverse("accounts:daily_hours"), {"hours": 12}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.daily_study_target_minutes, 12 * 60)

        session = LoginSession.objects.filter(user=self.user).order_by("-login_at").first()
        self.assertTrue(session.hours_collected)

    def test_daily_hours_view_syncs_already_existing_daily_timer(self):
        from apps.timetracker.models import DailyTimer

        self.client.login(email="checkin-tester@example.com", password="testpass123")

        # Simulate a DailyTimer that already existed for today with a stale goal
        # (e.g. created before this prompt existed, or before today's submission).
        DailyTimer.objects.create(
            user=self.user, date=timezone.localdate(), goal_minutes=1140, status=DailyTimer.Status.IDLE
        )

        with mock.patch("apps.accounts.forms.seconds_until_cutoff", return_value=23 * 3600):
            self.client.post(reverse("accounts:daily_hours"), {"hours": 6}, follow=True)

        daily_timer = DailyTimer.objects.get(user=self.user, date=timezone.localdate())
        self.assertEqual(daily_timer.goal_minutes, 6 * 60)
