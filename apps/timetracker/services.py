from datetime import datetime
from datetime import time as dtime
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.activity.services import log_activity

from .models import (
    Activity,
    BreakSession,
    DailySummary,
    DailyTimer,
    TimerEvent,
    TimerSession,
    WasteSession,
)

DEFAULT_GOAL_MINUTES = 240


class TimerStateError(Exception):
    """Raised when a timer action is attempted from an illegal state."""


def _build_label(activity=None, subject=None, topic=None):
    if topic:
        return f"{subject.name}: {topic.title}" if subject else topic.title
    if subject:
        return subject.name
    if activity:
        return activity.name
    return ""


def _record_event(daily_timer, event_type, occurred_at=None, activity=None, subject=None, topic=None, duration_seconds=None):
    TimerEvent.objects.create(
        user=daily_timer.user,
        daily_timer=daily_timer,
        event_type=event_type,
        occurred_at=occurred_at or timezone.now(),
        activity=activity,
        subject=subject,
        topic=topic,
        duration_seconds=duration_seconds,
        label=_build_label(activity, subject, topic),
    )


def _close_open_session(daily_timer, at=None):
    at = at or timezone.now()
    session = TimerSession.objects.filter(daily_timer=daily_timer, end_at__isnull=True).first()
    if not session:
        return None

    session.end_at = at
    session.duration_seconds = max(0, int((at - session.start_at).total_seconds()))
    session.save(update_fields=["end_at", "duration_seconds"])

    _record_event(
        daily_timer,
        TimerEvent.EventType.SESSION_ENDED,
        occurred_at=at,
        activity=session.activity,
        subject=session.subject,
        topic=session.topic,
        duration_seconds=session.duration_seconds,
    )

    minutes = round(session.duration_seconds / 60)
    log_activity(
        daily_timer.user,
        "timer_session",
        f"Logged {minutes} min on {session.activity.name}",
        url="/timer/",
        icon="bi-stopwatch",
    )

    return session


def _close_open_break(daily_timer, at=None):
    at = at or timezone.now()
    brk = BreakSession.objects.filter(daily_timer=daily_timer, end_at__isnull=True).first()
    if not brk:
        return None

    brk.end_at = at
    brk.duration_seconds = max(0, int((at - brk.start_at).total_seconds()))
    brk.save(update_fields=["end_at", "duration_seconds"])

    _record_event(daily_timer, TimerEvent.EventType.BREAK_ENDED, occurred_at=at, duration_seconds=brk.duration_seconds)

    return brk


def _maybe_log_break_overrun(daily_timer, brk):
    """If a break ran longer than its planned duration, log the overrun as Wasted time.

    Wasted time is no longer a manually start/stopped state — it's derived entirely from
    how much longer a break actually took than the user committed to when starting it.
    """
    overrun_seconds = max(brk.duration_seconds - brk.planned_minutes * 60, 0)
    if overrun_seconds <= 0:
        return None

    waste_start = brk.end_at - timedelta(seconds=overrun_seconds)
    waste = WasteSession.objects.create(
        user=daily_timer.user,
        daily_timer=daily_timer,
        start_at=waste_start,
        end_at=brk.end_at,
        duration_seconds=overrun_seconds,
        reason=f"Ran over break: {brk.reason}",
    )

    _record_event(daily_timer, TimerEvent.EventType.WASTE_STARTED, occurred_at=waste_start)
    _record_event(daily_timer, TimerEvent.EventType.WASTE_ENDED, occurred_at=brk.end_at, duration_seconds=overrun_seconds)

    return waste


def _generate_daily_summary(daily_timer):
    completed_minutes = round(
        sum(s.duration_seconds for s in TimerSession.objects.filter(daily_timer=daily_timer, end_at__isnull=False)) / 60
    )
    break_minutes = round(
        sum(b.duration_seconds for b in BreakSession.objects.filter(daily_timer=daily_timer, end_at__isnull=False)) / 60
    )
    waste_minutes = round(
        sum(w.duration_seconds for w in WasteSession.objects.filter(daily_timer=daily_timer, end_at__isnull=False)) / 60
    )

    missed_minutes = max(daily_timer.goal_minutes - completed_minutes, 0)
    completion_percent = (
        round(completed_minutes / daily_timer.goal_minutes * 100) if daily_timer.goal_minutes else 0
    )

    summary, _ = DailySummary.objects.update_or_create(
        user=daily_timer.user,
        date=daily_timer.date,
        defaults={
            "goal_minutes": daily_timer.goal_minutes,
            "completed_minutes": completed_minutes,
            "missed_minutes": missed_minutes,
            "break_minutes": break_minutes,
            "waste_minutes": waste_minutes,
            "completion_percent": completion_percent,
        },
    )
    return summary


def _rollover_close(daily_timer):
    tz = timezone.get_current_timezone()
    close_at = timezone.make_aware(datetime.combine(daily_timer.date, dtime(23, 59, 59)), tz)

    _close_open_session(daily_timer, at=close_at)
    stale_break = _close_open_break(daily_timer, at=close_at)
    if stale_break:
        _maybe_log_break_overrun(daily_timer, stale_break)

    _record_event(daily_timer, TimerEvent.EventType.DAY_CLOSED, occurred_at=close_at)

    daily_timer.status = DailyTimer.Status.CLOSED
    daily_timer.closed_at = timezone.now()
    daily_timer.save(update_fields=["status", "closed_at"])

    _generate_daily_summary(daily_timer)


def get_or_open_daily_timer(user):
    """The single entry point every timer-touching view/service call goes through.

    Returns today's DailyTimer, transparently closing out any stale open day(s)
    first (lazy midnight rollover — this project has no scheduled-job infra).
    """
    today = timezone.localdate()

    with transaction.atomic():
        existing = (
            DailyTimer.objects.select_for_update()
            .filter(user=user, date=today)
            .exclude(status=DailyTimer.Status.CLOSED)
            .first()
        )
        if existing:
            return existing

        stale_timers = (
            DailyTimer.objects.select_for_update()
            .filter(user=user)
            .exclude(status=DailyTimer.Status.CLOSED)
            .exclude(date=today)
            .order_by("date")
        )

        for stale in stale_timers:
            _rollover_close(stale)

        goal_minutes = getattr(user.profile, "daily_study_target_minutes", DEFAULT_GOAL_MINUTES)

        new_timer = DailyTimer.objects.create(
            user=user,
            date=today,
            goal_minutes=goal_minutes,
            status=DailyTimer.Status.IDLE,
        )
        _record_event(new_timer, TimerEvent.EventType.DAY_STARTED)

        return new_timer


def start_session(user, activity, subject=None, topic=None, notes=""):
    notes = (notes or "").strip()

    if activity.kind == Activity.Kind.BREAK:
        raise TimerStateError("Use the Take a Break button to start a break, not Start Session.")

    if activity.kind == Activity.Kind.STUDY and (subject is None or topic is None):
        raise TimerStateError("Select a Subject and Topic to start a Study session.")

    if activity.kind == Activity.Kind.OTHERS and not notes:
        raise TimerStateError("Describe what you're doing to start an Others session.")

    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status not in (DailyTimer.Status.IDLE, DailyTimer.Status.PAUSED):
            raise TimerStateError(
                f"Can't start a session while status is '{daily_timer.get_status_display()}'."
            )

        now = timezone.now()
        session = TimerSession.objects.create(
            user=user,
            daily_timer=daily_timer,
            activity=activity,
            subject=subject,
            topic=topic,
            start_at=now,
            notes=notes,
        )
        _record_event(
            daily_timer,
            TimerEvent.EventType.SESSION_STARTED,
            occurred_at=now,
            activity=activity,
            subject=subject,
            topic=topic,
        )

        daily_timer.status = DailyTimer.Status.RUNNING
        daily_timer.save(update_fields=["status"])

        return session


def pause_session(user):
    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status != DailyTimer.Status.RUNNING:
            raise TimerStateError(
                f"Can't pause — not currently running (status is '{daily_timer.get_status_display()}')."
            )

        session = _close_open_session(daily_timer)

        daily_timer.status = DailyTimer.Status.PAUSED
        daily_timer.save(update_fields=["status"])

        return session


def resume_session(user):
    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status != DailyTimer.Status.PAUSED:
            raise TimerStateError(f"Can't resume — status is '{daily_timer.get_status_display()}'.")

        last_session = TimerSession.objects.filter(daily_timer=daily_timer).order_by("-start_at").first()
        if not last_session:
            raise TimerStateError("Nothing to resume — start a session first.")

        now = timezone.now()
        session = TimerSession.objects.create(
            user=user,
            daily_timer=daily_timer,
            activity=last_session.activity,
            subject=last_session.subject,
            topic=last_session.topic,
            start_at=now,
            notes=last_session.notes,
        )
        _record_event(
            daily_timer,
            TimerEvent.EventType.SESSION_STARTED,
            occurred_at=now,
            activity=session.activity,
            subject=session.subject,
            topic=session.topic,
        )

        daily_timer.status = DailyTimer.Status.RUNNING
        daily_timer.save(update_fields=["status"])

        return session


def stop_session(user):
    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status not in (DailyTimer.Status.RUNNING, DailyTimer.Status.PAUSED):
            raise TimerStateError(f"Can't stop — status is '{daily_timer.get_status_display()}'.")

        if daily_timer.status == DailyTimer.Status.RUNNING:
            _close_open_session(daily_timer)

        daily_timer.status = DailyTimer.Status.IDLE
        daily_timer.save(update_fields=["status"])


def start_break(user, reason, planned_minutes):
    reason = (reason or "").strip()
    if not reason:
        raise TimerStateError("A reason is required to start a break.")

    try:
        planned_minutes = int(planned_minutes)
    except (TypeError, ValueError):
        planned_minutes = 0
    if planned_minutes < 1:
        raise TimerStateError("Enter how many minutes your break will be.")

    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status not in (
            DailyTimer.Status.IDLE,
            DailyTimer.Status.PAUSED,
            DailyTimer.Status.RUNNING,
        ):
            raise TimerStateError(f"Can't start a break — status is '{daily_timer.get_status_display()}'.")

        if daily_timer.status == DailyTimer.Status.RUNNING:
            _close_open_session(daily_timer)

        now = timezone.now()
        brk = BreakSession.objects.create(
            user=user,
            daily_timer=daily_timer,
            start_at=now,
            reason=reason,
            planned_minutes=planned_minutes,
        )
        _record_event(daily_timer, TimerEvent.EventType.BREAK_STARTED, occurred_at=now)

        daily_timer.status = DailyTimer.Status.ON_BREAK
        daily_timer.save(update_fields=["status"])

        return brk


def end_break(user):
    with transaction.atomic():
        daily_timer = get_or_open_daily_timer(user)

        if daily_timer.status != DailyTimer.Status.ON_BREAK:
            raise TimerStateError(f"Can't end a break — status is '{daily_timer.get_status_display()}'.")

        brk = _close_open_break(daily_timer)
        _maybe_log_break_overrun(daily_timer, brk)

        daily_timer.status = DailyTimer.Status.PAUSED
        daily_timer.save(update_fields=["status"])

        return brk


def today_timeline(user):
    daily_timer = get_or_open_daily_timer(user)
    return TimerEvent.objects.filter(daily_timer=daily_timer).select_related("activity", "subject", "topic")


def first_session_start_today(user):
    """The occurred_at of today's earliest SESSION_STARTED event, or None if nothing's started yet."""
    daily_timer = get_or_open_daily_timer(user)
    event = (
        TimerEvent.objects.filter(daily_timer=daily_timer, event_type=TimerEvent.EventType.SESSION_STARTED)
        .order_by("occurred_at")
        .first()
    )
    return event.occurred_at if event else None


def today_summary(user):
    daily_timer = get_or_open_daily_timer(user)
    now = timezone.now()

    sessions = TimerSession.objects.filter(daily_timer=daily_timer)
    completed_seconds = sum(
        s.duration_seconds if s.end_at else int((now - s.start_at).total_seconds()) for s in sessions
    )

    breaks = BreakSession.objects.filter(daily_timer=daily_timer)
    break_seconds = sum(
        b.duration_seconds if b.end_at else int((now - b.start_at).total_seconds()) for b in breaks
    )

    # WasteSession rows are always created already-closed (derived from a break's overrun at
    # the moment it ends) — there is no manually-started/open waste state anymore.
    waste_seconds = sum(w.duration_seconds for w in WasteSession.objects.filter(daily_timer=daily_timer))

    completed_minutes = round(completed_seconds / 60)
    break_minutes = round(break_seconds / 60)
    waste_minutes = round(waste_seconds / 60)
    goal_minutes = daily_timer.goal_minutes
    missed_minutes = max(goal_minutes - completed_minutes, 0)
    completion_percent = round(completed_minutes / goal_minutes * 100) if goal_minutes else 0

    current_session = (
        sessions.filter(end_at__isnull=True).select_related("activity", "subject", "topic").first()
    )
    current_break = breaks.filter(end_at__isnull=True).first()

    # The most recently touched session, open or closed — powers "Resume <activity>" while paused,
    # since current_session is only set while a session is actively open.
    last_session = sessions.select_related("activity").order_by("-start_at").first()

    return {
        "status": daily_timer.status,
        "goal_minutes": goal_minutes,
        "completed_minutes": completed_minutes,
        "missed_minutes": missed_minutes,
        "break_minutes": break_minutes,
        "waste_minutes": waste_minutes,
        "total_unslept_minutes": completed_minutes + break_minutes + waste_minutes,
        "completion_percent": completion_percent,
        "last_activity": last_session.activity.name if last_session else None,
        "current_activity": current_session.activity.name if current_session else None,
        "current_activity_id": current_session.activity_id if current_session else None,
        "current_subject_id": current_session.subject_id if current_session else None,
        "current_topic_id": current_session.topic_id if current_session else None,
        "current_session_start": current_session.start_at.isoformat() if current_session else None,
        "current_break_start": current_break.start_at.isoformat() if current_break else None,
        "current_break_planned_minutes": current_break.planned_minutes if current_break else None,
    }


def activity_stats(user, activity):
    sessions = TimerSession.objects.filter(user=user, activity=activity, end_at__isnull=False)

    total_seconds = sum(s.duration_seconds for s in sessions)
    session_count = sessions.count()
    avg_seconds = total_seconds / session_count if session_count else 0
    longest = sessions.order_by("-duration_seconds").first()
    last_session = sessions.order_by("-start_at").first()

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    def minutes_since(start_date):
        return round(
            sum(s.duration_seconds for s in sessions.filter(start_at__date__gte=start_date)) / 60
        )

    return {
        "total_minutes": round(total_seconds / 60),
        "session_count": session_count,
        "avg_session_minutes": round(avg_seconds / 60),
        "longest_session_minutes": round(longest.duration_seconds / 60) if longest else 0,
        "last_studied": last_session.start_at if last_session else None,
        "this_week_minutes": minutes_since(week_start),
        "this_month_minutes": minutes_since(month_start),
        "this_year_minutes": minutes_since(year_start),
    }


def historical_range_summary(user, start_date, end_date):
    """Aggregate per-day + per-activity totals across [start_date, end_date] inclusive.

    DailySummary rows only ever exist for closed/past days, so if today falls inside the
    range its row is computed live via today_summary() instead of read from the DB.
    """
    today = timezone.localdate()

    summaries_by_date = {
        s.date: s
        for s in DailySummary.objects.filter(user=user, date__gte=start_date, date__lte=end_date)
    }

    if start_date <= today <= end_date and today not in summaries_by_date:
        summaries_by_date[today] = today_summary(user)

    daily_breakdown = []
    current = start_date
    while current <= end_date:
        entry = summaries_by_date.get(current)

        if entry is None:
            row = {
                "goal_minutes": 0,
                "completed_minutes": 0,
                "missed_minutes": 0,
                "break_minutes": 0,
                "waste_minutes": 0,
                "completion_percent": 0,
                "status": "no_activity",
            }
        elif isinstance(entry, DailySummary):
            row = {
                "goal_minutes": entry.goal_minutes,
                "completed_minutes": entry.completed_minutes,
                "missed_minutes": entry.missed_minutes,
                "break_minutes": entry.break_minutes,
                "waste_minutes": entry.waste_minutes,
                "completion_percent": entry.completion_percent,
                "status": entry.status,
            }
        else:
            completed = entry["completed_minutes"]
            goal = entry["goal_minutes"]
            status = "no_activity" if completed == 0 else ("goal_met" if completed >= goal else "goal_missed")
            row = {
                "goal_minutes": goal,
                "completed_minutes": completed,
                "missed_minutes": entry["missed_minutes"],
                "break_minutes": entry["break_minutes"],
                "waste_minutes": entry["waste_minutes"],
                "completion_percent": entry["completion_percent"],
                "status": status,
            }

        row["date"] = current
        daily_breakdown.append(row)
        current += timedelta(days=1)

    total_days = len(daily_breakdown)
    days_goal_met = sum(1 for r in daily_breakdown if r["status"] == "goal_met")
    days_goal_missed = sum(1 for r in daily_breakdown if r["status"] == "goal_missed")
    days_no_activity = sum(1 for r in daily_breakdown if r["status"] == "no_activity")

    total_completed_minutes = sum(r["completed_minutes"] for r in daily_breakdown)
    total_break_minutes = sum(r["break_minutes"] for r in daily_breakdown)
    total_waste_minutes = sum(r["waste_minutes"] for r in daily_breakdown)
    total_missed_minutes = sum(r["missed_minutes"] for r in daily_breakdown)
    avg_completion_percent = (
        round(sum(r["completion_percent"] for r in daily_breakdown) / total_days) if total_days else 0
    )

    sessions = TimerSession.objects.filter(
        user=user,
        end_at__isnull=False,
        start_at__date__gte=start_date,
        start_at__date__lte=end_date,
    ).select_related("activity")

    activity_totals = {}
    for session in sessions:
        bucket = activity_totals.setdefault(
            session.activity_id, {"name": session.activity.name, "color": session.activity.color, "seconds": 0}
        )
        bucket["seconds"] += session.duration_seconds

    activity_distribution = sorted(
        (
            {
                "activity_id": activity_id,
                "name": bucket["name"],
                "color": bucket["color"],
                "total_minutes": round(bucket["seconds"] / 60),
            }
            for activity_id, bucket in activity_totals.items()
        ),
        key=lambda row: row["total_minutes"],
        reverse=True,
    )
    grand_total_minutes = sum(row["total_minutes"] for row in activity_distribution) or 1
    for row in activity_distribution:
        row["percent"] = round(row["total_minutes"] / grand_total_minutes * 100)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "daily_breakdown": daily_breakdown,
        "total_days": total_days,
        "days_goal_met": days_goal_met,
        "days_goal_missed": days_goal_missed,
        "days_no_activity": days_no_activity,
        "total_completed_minutes": total_completed_minutes,
        "total_break_minutes": total_break_minutes,
        "total_waste_minutes": total_waste_minutes,
        "total_missed_minutes": total_missed_minutes,
        "avg_completion_percent": avg_completion_percent,
        "activity_distribution": activity_distribution,
    }
