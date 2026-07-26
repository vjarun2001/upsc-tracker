from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from . import services
from .models import Activity, BreakSession, DailySummary, DailyTimer, TimerSession, WasteSession

User = get_user_model()


class TimeTrackerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="timer-tester@example.com", password="testpass123")
        self.activity = Activity.objects.create(user=self.user, name="GS2")


class DefaultActivitySeedingTests(TestCase):
    def test_new_user_gets_four_default_activities(self):
        user = User.objects.create_user(email="fresh-user@example.com", password="testpass123")

        kinds = set(Activity.objects.filter(user=user).values_list("kind", flat=True))
        self.assertEqual(
            kinds,
            {Activity.Kind.STUDY, Activity.Kind.TUITION, Activity.Kind.BREAK, Activity.Kind.OTHERS},
        )


class StateMachineTests(TimeTrackerTestCase):
    def test_start_session_moves_idle_to_running(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        self.assertEqual(daily_timer.status, DailyTimer.Status.IDLE)

        services.start_session(self.user, self.activity)

        daily_timer.refresh_from_db()
        self.assertEqual(daily_timer.status, DailyTimer.Status.RUNNING)
        self.assertEqual(TimerSession.objects.filter(daily_timer=daily_timer, end_at__isnull=True).count(), 1)

    def test_pause_then_resume_reuses_last_activity(self):
        services.start_session(self.user, self.activity)
        services.pause_session(self.user)

        daily_timer = services.get_or_open_daily_timer(self.user)
        self.assertEqual(daily_timer.status, DailyTimer.Status.PAUSED)

        session = services.resume_session(self.user)
        self.assertEqual(session.activity_id, self.activity.pk)
        daily_timer.refresh_from_db()
        self.assertEqual(daily_timer.status, DailyTimer.Status.RUNNING)

    def test_stop_session_closes_open_session_and_records_duration(self):
        services.start_session(self.user, self.activity)
        services.stop_session(self.user)

        session = TimerSession.objects.get(daily_timer__user=self.user)
        self.assertIsNotNone(session.end_at)
        self.assertGreaterEqual(session.duration_seconds, 0)

        daily_timer = services.get_or_open_daily_timer(self.user)
        self.assertEqual(daily_timer.status, DailyTimer.Status.IDLE)

    def test_cannot_start_session_while_running(self):
        services.start_session(self.user, self.activity)
        with self.assertRaises(services.TimerStateError):
            services.start_session(self.user, self.activity)

    def test_cannot_resume_without_a_prior_session(self):
        services.get_or_open_daily_timer(self.user)
        with self.assertRaises(services.TimerStateError):
            services.resume_session(self.user)

    def test_break_implicitly_closes_open_session(self):
        services.start_session(self.user, self.activity)
        services.start_break(self.user, reason="Tea", planned_minutes=10)

        session = TimerSession.objects.get(daily_timer__user=self.user)
        self.assertIsNotNone(session.end_at)

        daily_timer = services.get_or_open_daily_timer(self.user)
        self.assertEqual(daily_timer.status, DailyTimer.Status.ON_BREAK)

        services.end_break(self.user)
        daily_timer.refresh_from_db()
        self.assertEqual(daily_timer.status, DailyTimer.Status.PAUSED)

    def test_start_session_requires_subject_and_topic_for_study_activity(self):
        study = Activity.objects.get(user=self.user, kind=Activity.Kind.STUDY)
        with self.assertRaises(services.TimerStateError):
            services.start_session(self.user, study)

    def test_start_session_requires_notes_for_others_activity(self):
        others = Activity.objects.get(user=self.user, kind=Activity.Kind.OTHERS)
        with self.assertRaises(services.TimerStateError):
            services.start_session(self.user, others)

        session = services.start_session(self.user, others, notes="Helping a friend move")
        self.assertEqual(session.notes, "Helping a friend move")

    def test_start_break_requires_reason_and_planned_minutes(self):
        with self.assertRaises(services.TimerStateError):
            services.start_break(self.user, reason="", planned_minutes=10)

    def test_cannot_start_session_with_break_activity(self):
        break_activity = Activity.objects.get(user=self.user, kind=Activity.Kind.BREAK)
        with self.assertRaises(services.TimerStateError):
            services.start_session(self.user, break_activity)
        with self.assertRaises(services.TimerStateError):
            services.start_break(self.user, reason="Tea", planned_minutes=0)


class BreakOverrunTests(TimeTrackerTestCase):
    def test_returning_within_planned_duration_logs_no_wasted_time(self):
        services.start_break(self.user, reason="Tea", planned_minutes=10)
        brk = BreakSession.objects.get(daily_timer__user=self.user)
        brk.start_at = timezone.now() - timedelta(minutes=5)
        brk.save(update_fields=["start_at"])

        services.end_break(self.user)

        self.assertEqual(WasteSession.objects.filter(user=self.user).count(), 0)

    def test_returning_late_logs_overrun_as_wasted_time(self):
        services.start_break(self.user, reason="Tea", planned_minutes=10)
        brk = BreakSession.objects.get(daily_timer__user=self.user)
        brk.start_at = timezone.now() - timedelta(minutes=15)
        brk.save(update_fields=["start_at"])

        services.end_break(self.user)

        waste = WasteSession.objects.get(user=self.user)
        self.assertAlmostEqual(waste.duration_seconds, 5 * 60, delta=2)


class ConcurrencyTests(TimeTrackerTestCase):
    def test_db_rejects_second_open_session_on_same_daily_timer(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        TimerSession.objects.create(
            user=self.user, daily_timer=daily_timer, activity=self.activity, start_at=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TimerSession.objects.create(
                    user=self.user, daily_timer=daily_timer, activity=self.activity, start_at=timezone.now()
                )

    def test_db_rejects_second_open_break_on_same_daily_timer(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        BreakSession.objects.create(user=self.user, daily_timer=daily_timer, start_at=timezone.now())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BreakSession.objects.create(user=self.user, daily_timer=daily_timer, start_at=timezone.now())


class RolloverTests(TimeTrackerTestCase):
    def test_stale_open_day_is_force_closed_and_summarized(self):
        stale_date = timezone.localdate() - timedelta(days=3)
        stale_timer = DailyTimer.objects.create(
            user=self.user, date=stale_date, goal_minutes=240, status=DailyTimer.Status.RUNNING
        )
        TimerSession.objects.create(
            user=self.user,
            daily_timer=stale_timer,
            activity=self.activity,
            start_at=timezone.make_aware(timezone.datetime.combine(stale_date, timezone.datetime.min.time())),
        )

        today_timer = services.get_or_open_daily_timer(self.user)

        stale_timer.refresh_from_db()
        self.assertEqual(stale_timer.status, DailyTimer.Status.CLOSED)
        self.assertFalse(TimerSession.objects.filter(daily_timer=stale_timer, end_at__isnull=True).exists())

        summary = DailySummary.objects.get(user=self.user, date=stale_date)
        self.assertEqual(summary.completed_minutes, 1440)  # 00:00:00 -> 23:59:59, rounds up to a full day
        self.assertEqual(summary.status, "goal_met")

        self.assertEqual(today_timer.date, timezone.localdate())
        self.assertEqual(today_timer.status, DailyTimer.Status.IDLE)

    def test_stale_open_break_is_force_closed_with_overrun_logged_as_waste(self):
        stale_date = timezone.localdate() - timedelta(days=2)
        stale_timer = DailyTimer.objects.create(
            user=self.user, date=stale_date, goal_minutes=240, status=DailyTimer.Status.ON_BREAK
        )
        BreakSession.objects.create(
            user=self.user,
            daily_timer=stale_timer,
            start_at=timezone.make_aware(timezone.datetime.combine(stale_date, timezone.datetime.min.time())),
            planned_minutes=10,
        )

        services.get_or_open_daily_timer(self.user)

        brk = BreakSession.objects.get(daily_timer=stale_timer)
        self.assertIsNotNone(brk.end_at)
        waste = WasteSession.objects.get(daily_timer=stale_timer)
        self.assertEqual(waste.duration_seconds, brk.duration_seconds - 10 * 60)

    def test_get_or_open_daily_timer_is_idempotent_for_today(self):
        first = services.get_or_open_daily_timer(self.user)
        second = services.get_or_open_daily_timer(self.user)
        self.assertEqual(first.pk, second.pk)


class SummaryAndStatsTests(TimeTrackerTestCase):
    def test_today_summary_reflects_open_session_elapsed_time(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        start = timezone.now() - timedelta(minutes=10)
        TimerSession.objects.create(user=self.user, daily_timer=daily_timer, activity=self.activity, start_at=start)
        daily_timer.status = DailyTimer.Status.RUNNING
        daily_timer.save(update_fields=["status"])

        summary = services.today_summary(self.user)
        self.assertEqual(summary["completed_minutes"], 10)
        self.assertEqual(summary["current_activity"], "GS2")

    def test_activity_stats_totals(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        now = timezone.now()
        TimerSession.objects.create(
            user=self.user,
            daily_timer=daily_timer,
            activity=self.activity,
            start_at=now - timedelta(minutes=45),
            end_at=now,
            duration_seconds=45 * 60,
        )

        stats = services.activity_stats(self.user, self.activity)
        self.assertEqual(stats["total_minutes"], 45)
        self.assertEqual(stats["session_count"], 1)
        self.assertEqual(stats["avg_session_minutes"], 45)

    def test_historical_range_summary_aggregates_past_and_today(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        DailySummary.objects.create(
            user=self.user,
            date=yesterday,
            goal_minutes=240,
            completed_minutes=180,
            missed_minutes=60,
            break_minutes=20,
            waste_minutes=5,
            completion_percent=75,
        )

        daily_timer = services.get_or_open_daily_timer(self.user)
        now = timezone.now()
        TimerSession.objects.create(
            user=self.user,
            daily_timer=daily_timer,
            activity=self.activity,
            start_at=now - timedelta(minutes=30),
            end_at=now,
            duration_seconds=30 * 60,
        )

        today = timezone.localdate()
        summary = services.historical_range_summary(self.user, yesterday, today)

        self.assertEqual(summary["total_days"], 2)
        self.assertEqual(summary["total_completed_minutes"], 210)
        # both days fall short of the 240-minute default goal: yesterday's persisted 180m and
        # today's live 30m (today is computed on the fly via today_summary(), not read from DB)
        self.assertEqual(summary["days_goal_missed"], 2)
        self.assertEqual(len(summary["activity_distribution"]), 1)
        self.assertEqual(summary["activity_distribution"][0]["name"], "GS2")
        self.assertEqual(summary["activity_distribution"][0]["total_minutes"], 30)


class ActivityCRUDTests(TimeTrackerTestCase):
    def test_activity_with_sessions_cannot_be_hard_deleted(self):
        daily_timer = services.get_or_open_daily_timer(self.user)
        TimerSession.objects.create(
            user=self.user,
            daily_timer=daily_timer,
            activity=self.activity,
            start_at=timezone.now(),
            end_at=timezone.now(),
        )

        with self.assertRaises(ProtectedError):
            self.activity.delete()

    def test_activity_list_view_requires_login(self):
        response = self.client.get("/timer/activities/")
        self.assertEqual(response.status_code, 302)

    def test_activity_list_view_shows_active_and_archived(self):
        from apps.accounts.models import LoginSession

        archived = Activity.objects.create(user=self.user, name="Old Habit", is_active=False)
        self.client.force_login(self.user)
        # force_login fires user_logged_in, which creates a LoginSession that the
        # DailyCheckInMiddleware would otherwise redirect away to the hours prompt.
        LoginSession.objects.filter(user=self.user).update(hours_collected=True)

        response = self.client.get("/timer/activities/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GS2")
        self.assertContains(response, "Old Habit")
        self.assertNotIn(archived, response.context["active_activities"])
