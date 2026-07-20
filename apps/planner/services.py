from datetime import timedelta

from django.utils import timezone

from apps.activity.services import log_activity

from .models import PomodoroSession


def mark_task_completed(task):
    """Mark a task done, syncing its linked tracker log and the activity feed."""
    if not task.is_completed:
        task.is_completed = True
        task.save(update_fields=["is_completed"])

    log_activity(
        task.user,
        "task_completed",
        f"Completed task: {task.title}",
        url="/planner/",
        icon="bi-check-square",
    )

    if task.tracker_id:
        log, _ = task.tracker.logs.get_or_create(date=task.date)
        if not log.value:
            log.value = task.tracker.target_value if task.tracker.kind != task.tracker.Kind.BOOLEAN else 1
            log.save(update_fields=["value"])


def timer_stats(user, days=7):
    since = timezone.localdate() - timedelta(days=days - 1)

    sessions = PomodoroSession.objects.filter(user=user, started_at__date__gte=since)

    focus_sessions = [s for s in sessions if s.session_type == PomodoroSession.SessionType.FOCUS]
    break_sessions = [
        s
        for s in sessions
        if s.session_type
        in (PomodoroSession.SessionType.SHORT_BREAK, PomodoroSession.SessionType.LONG_BREAK)
    ]

    focus_seconds = sum(s.actual_duration_seconds for s in focus_sessions if s.is_completed)
    break_seconds = sum(s.actual_duration_seconds for s in break_sessions if s.is_completed)

    completed_count = sum(1 for s in sessions if s.is_completed)

    avg_focus_seconds = focus_seconds / days if days else 0

    return {
        "focus_time_minutes": round(focus_seconds / 60),
        "sessions_completed": completed_count,
        "break_time_minutes": round(break_seconds / 60),
        "avg_focus_minutes": round(avg_focus_seconds / 60),
    }
