import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.timetracker import services
from apps.timetracker.models import Activity, DailySummary, DailyTimer, TimerSession

User = get_user_model()

DEFAULT_ACTIVITIES = [
    ("GS1", "#0d6efd", "bi-globe-asia-australia"),
    ("GS2", "#6f42c1", "bi-bank"),
    ("GS3", "#198754", "bi-graph-up-arrow"),
    ("GS4", "#fd7e14", "bi-emoji-smile"),
    ("Optional", "#dc3545", "bi-mortarboard"),
    ("CSAT", "#20c997", "bi-calculator"),
    ("Newspaper", "#6c757d", "bi-newspaper"),
    ("Current Affairs", "#0dcaf0", "bi-broadcast"),
    ("Revision", "#ffc107", "bi-arrow-repeat"),
    ("Answer Writing", "#d63384", "bi-pencil-square"),
    ("PYQs", "#495057", "bi-clock-history"),
    ("Mock Test", "#f0635a", "bi-trophy"),
]

DAY_ARCHETYPES = [
    # (completion_ratio, break_minutes, waste_minutes) — cycled across seeded days for variety
    (0.95, 45, 10),
    (0.55, 60, 40),
    (0.80, 30, 15),
    (0.30, 20, 70),
    (1.05, 50, 5),
    (0.65, 40, 25),
    (0.0, 0, 0),  # a rest day with no logged activity
]


class Command(BaseCommand):
    help = "Seed realistic sample Activities and historical Time Tracker data for local demoing."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of the user to seed data for.")
        parser.add_argument("--days", type=int, default=14, help="How many past days of history to generate.")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email=options["email"])
        except User.DoesNotExist as exc:
            raise CommandError(f"No user with email {options['email']!r}.") from exc

        activities = []
        for name, color, icon in DEFAULT_ACTIVITIES:
            activity, _ = Activity.objects.get_or_create(user=user, name=name, defaults={"color": color, "icon": icon})
            activities.append(activity)

        goal_minutes = getattr(user.profile, "daily_study_target_minutes", services.DEFAULT_GOAL_MINUTES)
        today = timezone.localdate()
        days = options["days"]
        created_days = 0

        for offset in range(days, 0, -1):
            day = today - timedelta(days=offset)
            if DailyTimer.objects.filter(user=user, date=day).exists():
                continue

            ratio, break_minutes, waste_minutes = DAY_ARCHETYPES[offset % len(DAY_ARCHETYPES)]
            completed_minutes = round(goal_minutes * ratio)

            daily_timer = DailyTimer.objects.create(
                user=user,
                date=day,
                goal_minutes=goal_minutes,
                status=DailyTimer.Status.CLOSED,
                closed_at=timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())),
            )

            remaining = completed_minutes
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time())) + timedelta(hours=6)
            cursor = day_start
            while remaining > 0:
                chunk = min(remaining, random.randint(30, 90))
                activity = random.choice(activities)
                start_at = cursor
                end_at = start_at + timedelta(minutes=chunk)
                TimerSession.objects.create(
                    user=user,
                    daily_timer=daily_timer,
                    activity=activity,
                    start_at=start_at,
                    end_at=end_at,
                    duration_seconds=chunk * 60,
                )
                cursor = end_at + timedelta(minutes=10)
                remaining -= chunk

            missed_minutes = max(goal_minutes - completed_minutes, 0)
            completion_percent = round(completed_minutes / goal_minutes * 100) if goal_minutes else 0

            DailySummary.objects.update_or_create(
                user=user,
                date=day,
                defaults={
                    "goal_minutes": goal_minutes,
                    "completed_minutes": completed_minutes,
                    "missed_minutes": missed_minutes,
                    "break_minutes": break_minutes,
                    "waste_minutes": waste_minutes,
                    "completion_percent": completion_percent,
                },
            )
            created_days += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(activities)} activities and {created_days} day(s) of history for {user.email}."
            )
        )
