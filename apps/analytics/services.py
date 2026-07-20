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


def _focus_pomodoro_sessions(user, **filters):
    from apps.planner.models import PomodoroSession

    return PomodoroSession.objects.filter(
        user=user,
        is_completed=True,
        session_type=PomodoroSession.SessionType.FOCUS,
        **filters,
    ).select_related("subject")


def minutes_per_subject(user):
    from apps.study.models import StudySession

    sessions = StudySession.objects.filter(user=user).select_related("subject")

    totals = {}
    for session in sessions:
        totals[session.subject.name] = totals.get(session.subject.name, 0) + session.duration_minutes

    for session in _focus_pomodoro_sessions(user):
        if not session.subject_id:
            continue
        minutes = round(session.actual_duration_seconds / 60)
        totals[session.subject.name] = totals.get(session.subject.name, 0) + minutes

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

    for session in _focus_pomodoro_sessions(user, started_at__date__gte=days[0]):
        day = session.started_at.date()
        if day in totals:
            totals[day] += round(session.actual_duration_seconds / 60)

    labels = [day.strftime("%d %b") for day in days]
    values = [totals[day] for day in days]

    return labels, values


def weekly_study_minutes(user):
    from apps.study.models import StudySession

    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    sessions = StudySession.objects.filter(user=user, start_time__date__gte=monday)

    totals = {day: 0 for day in days}
    for session in sessions:
        day = session.start_time.date() if hasattr(session.start_time, "date") else session.start_time
        if day in totals:
            totals[day] += session.duration_minutes

    for session in _focus_pomodoro_sessions(user, started_at__date__gte=monday):
        day = session.started_at.date()
        if day in totals:
            totals[day] += round(session.actual_duration_seconds / 60)

    labels = [day.strftime("%a") for day in days]
    minutes = [totals[day] for day in days]

    return labels, minutes


def daily_study_breakdown(user):
    """Per-day (current week) list of {label, minutes} entries for the Study Hours chart click-through."""
    from apps.study.models import StudySession

    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    breakdown = {day: {} for day in days}

    def add(day, label, minutes):
        if day not in breakdown or not minutes:
            return
        breakdown[day][label] = breakdown[day].get(label, 0) + minutes

    for session in StudySession.objects.filter(user=user, start_time__date__gte=monday).select_related(
        "subject", "topic"
    ):
        day = session.start_time.date()
        label = session.subject.name
        if session.topic:
            label = f"{label}: {session.topic.title}"
        add(day, label, session.duration_minutes)

    for session in _focus_pomodoro_sessions(user, started_at__date__gte=monday).select_related(
        "task", "subject", "topic"
    ):
        day = session.started_at.date()
        minutes = round(session.actual_duration_seconds / 60)

        if session.topic:
            label = session.topic.title
            if session.subject:
                label = f"{session.subject.name}: {label}"
        elif session.subject:
            label = session.subject.name
        elif session.task:
            label = session.task.title
        else:
            label = "Focus session"

        add(day, label, minutes)

    return {
        day.isoformat(): sorted(
            [{"label": label, "minutes": minutes} for label, minutes in entries.items()],
            key=lambda e: e["minutes"],
            reverse=True,
        )
        for day, entries in breakdown.items()
    }


def task_trend(user, n=14):
    from apps.planner.models import DailyTask

    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(n - 1, -1, -1)]

    tasks = DailyTask.objects.filter(user=user, date__gte=days[0], date__lte=today)

    done_by_day = {day: 0 for day in days}
    pending_by_day = {day: 0 for day in days}

    for task in tasks:
        if task.date in done_by_day:
            if task.is_completed:
                done_by_day[task.date] += 1
            else:
                pending_by_day[task.date] += 1

    labels = [day.strftime("%d %b") for day in days]

    return labels, [done_by_day[d] for d in days], [pending_by_day[d] for d in days]


def revision_activity(user, n=14):
    from apps.revision.models import RevisionSchedule

    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(n - 1, -1, -1)]

    entries = RevisionSchedule.objects.filter(
        user=user, scheduled_date__gte=days[0], scheduled_date__lte=today
    )

    revised_by_day = {day: 0 for day in days}
    overdue_by_day = {day: 0 for day in days}

    for entry in entries:
        if entry.scheduled_date not in revised_by_day:
            continue
        if entry.is_done:
            revised_by_day[entry.scheduled_date] += 1
        elif entry.scheduled_date < today:
            overdue_by_day[entry.scheduled_date] += 1

    labels = [day.strftime("%d %b") for day in days]

    return labels, [revised_by_day[d] for d in days], [overdue_by_day[d] for d in days]


def revision_completion_summary(user):
    from apps.revision.models import RevisionSchedule

    total = RevisionSchedule.objects.filter(user=user).count()

    if not total:
        return 0

    done = RevisionSchedule.objects.filter(user=user, is_done=True).count()

    return round(done / total * 100)


def confidence_split(user):
    from apps.study.models import Topic

    topics = Topic.objects.filter(subject__user=user)

    counts = {"not_set": 0, "low": 0, "medium": 0, "high": 0}
    for topic in topics:
        key = topic.confidence or "not_set"
        counts[key] = counts.get(key, 0) + 1

    return counts


def syllabus_progress_by_subject(user):
    from apps.study.models import Subject, Topic

    subjects = Subject.objects.filter(user=user).prefetch_related("topics")

    rows = []
    for subject in subjects:
        total = subject.topics.count()
        if not total:
            continue
        done = subject.topics.filter(status=Topic.Status.COMPLETED).count()
        rows.append(
            {
                "name": subject.name,
                "color": subject.color,
                "completed_percent": round(done / total * 100),
                "not_started_percent": 100 - round(done / total * 100),
            }
        )

    return rows


def mock_test_trend(user):
    from apps.mocktest.models import MockTest

    tests = MockTest.objects.filter(user=user).order_by("test_date")

    labels = [t.test_date.strftime("%d %b") for t in tests]
    marks = [float(t.obtained_marks) for t in tests]
    accuracy = [t.accuracy_percent for t in tests]

    return labels, marks, accuracy


def routine_minutes_today(user):
    from apps.tracker.models import Tracker

    today = timezone.localdate()
    trackers = Tracker.objects.filter(
        user=user, is_active=True, kind=Tracker.Kind.DURATION
    )

    labels = []
    values = []

    for tracker in trackers:
        log = tracker.logs.filter(date=today).first()
        labels.append(tracker.name)
        values.append(log.value if log else 0)

    return labels, values


def build_daily_recap(user):
    from apps.accounts.services import today_seconds as accounts_today_seconds
    from apps.goals.models import Goal
    from apps.mocktest.models import MockTest
    from apps.planner.models import DailyTask, PomodoroSession
    from apps.tracker.models import Tracker, TrackerLog

    today = timezone.localdate()

    from apps.study.models import StudySession, Topic

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

    topics_done_today = Topic.objects.filter(
        subject__user=user, status=Topic.Status.COMPLETED, completed_at__date=today
    ).count()
    goals_done_today = Goal.objects.filter(
        user=user, is_completed=True, completed_at__date=today
    ).count()

    trackers_total = Tracker.objects.filter(user=user, is_active=True).count()
    trackers_logged = TrackerLog.objects.filter(
        tracker__user=user, tracker__is_active=True, date=today, value__gt=0
    ).count()

    meals_logged = TrackerLog.objects.filter(
        tracker__user=user,
        tracker__kind=Tracker.Kind.BOOLEAN,
        tracker__name__in=["Breakfast", "Lunch", "Dinner"],
        date=today,
        value__gt=0,
    ).count()

    mock_test_today = MockTest.objects.filter(user=user, test_date=today).exists()

    sleep_log = TrackerLog.objects.filter(
        tracker__user=user, tracker__name__iexact="sleep", date=today
    ).select_related("tracker").first()

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
    if trackers_total:
        highlights.append(f"Logged {trackers_logged}/{trackers_total} trackers")
    if meals_logged:
        highlights.append(f"Logged {meals_logged}/3 meals")
    if sleep_log:
        highlights.append(f"Slept {round(sleep_log.value / 60, 1)}h last night")
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

    daily_target_minutes = user.profile.daily_study_target_minutes or 240

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
    from apps.study.models import Subject, Topic

    subjects = Subject.objects.filter(user=user).prefetch_related("topics")

    labels = []
    percentages = []

    for subject in subjects:
        total = subject.topics.count()
        if not total:
            continue
        done = subject.topics.filter(status=Topic.Status.COMPLETED).count()
        labels.append(subject.name)
        percentages.append(round(done / total * 100, 1))

    return labels, percentages
