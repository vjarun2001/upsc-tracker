from datetime import timedelta

from django.db.models.functions import TruncDate
from django.utils import timezone


def get_active_dates(user):
    from apps.planner.models import PomodoroSession
    from apps.study.models import StudySession

    study_dates = set(
        StudySession.objects.filter(user=user)
        .annotate(d=TruncDate("start_time"))
        .values_list("d", flat=True)
    )

    pomodoro_dates = set(
        PomodoroSession.objects.filter(user=user, is_completed=True)
        .annotate(d=TruncDate("started_at"))
        .values_list("d", flat=True)
    )

    return study_dates | pomodoro_dates


def compute_current_streak(user):
    dates = get_active_dates(user)

    if not dates:
        return 0

    today = timezone.localdate()

    if today not in dates and (today - timedelta(days=1)) not in dates:
        return 0

    streak = 0
    cursor = today if today in dates else today - timedelta(days=1)

    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def minutes_per_subject(user):
    from apps.study.models import StudySession

    sessions = StudySession.objects.filter(user=user).select_related("subject")

    totals = {}
    for session in sessions:
        totals[session.subject.name] = totals.get(session.subject.name, 0) + session.duration_minutes

    return list(totals.keys()), list(totals.values())


def daily_minutes_last_n_days(user, n=14):
    from apps.study.models import StudySession

    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(n - 1, -1, -1)]

    sessions = StudySession.objects.filter(user=user)

    totals = {day: 0 for day in days}
    for session in sessions:
        day = session.start_time.date() if hasattr(session.start_time, "date") else session.start_time
        if day in totals:
            totals[day] += session.duration_minutes

    labels = [day.strftime("%d %b") for day in days]
    values = [totals[day] for day in days]

    return labels, values


def mock_test_trend(user):
    from apps.mocktest.models import MockTest

    tests = MockTest.objects.filter(user=user).order_by("test_date")

    labels = [t.test_date.strftime("%d %b") for t in tests]
    marks = [float(t.obtained_marks) for t in tests]
    accuracy = [t.accuracy_percent for t in tests]

    return labels, marks, accuracy


def routine_minutes_today(user):
    from apps.routines.models import Routine

    today = timezone.localdate()
    routines = Routine.objects.filter(user=user, is_active=True)

    labels = []
    values = []

    for routine in routines:
        log = routine.logs.filter(date=today).first()
        labels.append(routine.name)
        values.append(log.minutes_spent if log else 0)

    return labels, values


def build_daily_recap(user):
    from apps.accounts.services import today_seconds as accounts_today_seconds
    from apps.activity.services import get_today_activity
    from apps.mocktest.models import MockTest
    from apps.planner.models import DailyTask, PomodoroSession
    from apps.routines.models import Routine, RoutineLog
    from apps.wellness.models import Habit, HabitLog, MealLog, SleepLog

    today = timezone.localdate()

    from apps.study.models import StudySession

    study_minutes = sum(
        s.duration_minutes
        for s in StudySession.objects.filter(user=user, start_time__date=today)
    )
    pomodoro_minutes = sum(
        round(p.actual_duration_seconds / 60)
        for p in PomodoroSession.objects.filter(
            user=user,
            is_completed=True,
            started_at__date=today,
            session_type="focus",
        )
    )
    total_study_minutes = study_minutes + pomodoro_minutes

    tasks_qs = DailyTask.objects.filter(user=user, date=today)
    tasks_total = tasks_qs.count()
    tasks_done = tasks_qs.filter(is_completed=True).count()

    verb_counts = {}
    for activity in get_today_activity(user):
        verb_counts[activity.verb] = verb_counts.get(activity.verb, 0) + 1

    topics_done_today = verb_counts.get("topic_completed", 0)
    goals_done_today = verb_counts.get("goal_completed", 0)

    routines_total = Routine.objects.filter(user=user, is_active=True).count()
    routines_logged = RoutineLog.objects.filter(
        routine__user=user, routine__is_active=True, date=today
    ).count()

    habits_total = Habit.objects.filter(user=user, is_active=True).count()
    habits_done = HabitLog.objects.filter(
        habit__user=user, date=today, is_done=True
    ).count()

    meals_logged = MealLog.objects.filter(user=user, date=today, eaten=True).count()

    mock_test_today = MockTest.objects.filter(user=user, test_date=today).exists()

    sleep_log = SleepLog.objects.filter(user=user, date=today).first()

    streak = compute_current_streak(user)
    logged_in_minutes = round(accounts_today_seconds(user) / 60)

    highlights = []

    if total_study_minutes:
        highlights.append(f"Studied {total_study_minutes} min today")
    if tasks_total:
        highlights.append(f"Completed {tasks_done}/{tasks_total} planned tasks")
    if topics_done_today:
        highlights.append(f"Completed {topics_done_today} topic(s)")
    if goals_done_today:
        highlights.append(f"Completed {goals_done_today} goal(s)")
    if routines_total:
        highlights.append(f"Logged {routines_logged}/{routines_total} routines")
    if habits_total:
        highlights.append(f"Completed {habits_done}/{habits_total} habits")
    if meals_logged:
        highlights.append(f"Logged {meals_logged}/3 meals")
    if sleep_log:
        highlights.append(f"Slept {sleep_log.hours}h last night")
    if mock_test_today:
        highlights.append("Took a mock test today")
    if logged_in_minutes:
        highlights.append(f"Logged in for {logged_in_minutes} min today")
    if streak:
        highlights.append(f"\U0001f525 {streak}-day streak")

    if total_study_minutes >= 120:
        headline = "Excellent, focused day! Keep this momentum going."
    elif total_study_minutes >= 60:
        headline = "Solid effort today."
    elif total_study_minutes > 0:
        headline = "A light day — tomorrow's a fresh start."
    else:
        headline = "No study activity logged yet today."

    daily_target_minutes = 240

    return {
        "headline": headline,
        "highlights": highlights,
        "total_study_minutes": total_study_minutes,
        "logged_in_minutes": logged_in_minutes,
        "streak": streak,
        "daily_target_minutes": daily_target_minutes,
        "study_percent": min(100, round(total_study_minutes / daily_target_minutes * 100)),
    }


def topic_completion_per_subject(user):
    from apps.study.models import Subject

    subjects = Subject.objects.filter(user=user).prefetch_related("topics")

    labels = []
    percentages = []

    for subject in subjects:
        total = subject.topics.count()
        if not total:
            continue
        done = subject.topics.filter(is_completed=True).count()
        labels.append(subject.name)
        percentages.append(round(done / total * 100, 1))

    return labels, percentages
