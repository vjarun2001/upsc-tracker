import json
from datetime import date as ddate
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.common.utils import minutes_to_hours
from apps.study.models import Subject, Topic

from . import services
from .forms import ActivityForm
from .models import Activity, DailySummary, TimerSession

HISTORY_RANGE_DAYS = {"day": 0, "week": 6, "month": 29, "year": 364}
MAX_CUSTOM_RANGE_DAYS = 365


@login_required
def timer_page(request):
    daily_timer = services.get_or_open_daily_timer(request.user)

    # Break is triggered via its own dedicated reason+duration form, not the Activity picker.
    activities = Activity.objects.filter(user=request.user, is_active=True).exclude(kind=Activity.Kind.BREAK)
    subjects = Subject.objects.filter(user=request.user).prefetch_related("topics")

    topics_by_subject = {
        subject.pk: [{"id": topic.pk, "title": topic.title} for topic in subject.topics.all()]
        for subject in subjects
    }

    recent_sessions = TimerSession.objects.filter(
        daily_timer=daily_timer,
        end_at__isnull=False,
    ).select_related("activity", "subject", "topic")[:10]

    return render(
        request,
        "timetracker/timer.html",
        {
            "activities": activities,
            "subjects": subjects,
            "topics_by_subject": topics_by_subject,
            "recent_sessions": recent_sessions,
            "initial_summary": services.today_summary(request.user),
        },
    )


@login_required
def timeline_page(request):
    services.get_or_open_daily_timer(request.user)

    events = services.today_timeline(request.user)

    recent_summaries = DailySummary.objects.filter(user=request.user)[:14]

    return render(
        request,
        "timetracker/timeline.html",
        {
            "events": events,
            "recent_summaries": recent_summaries,
        },
    )


@login_required
def history_view(request):
    range_key = request.GET.get("range", "week")
    today = timezone.localdate()

    if range_key == "custom":
        try:
            start_date = ddate.fromisoformat(request.GET.get("start", ""))
            end_date = ddate.fromisoformat(request.GET.get("end", ""))
        except ValueError:
            range_key = "week"
            start_date, end_date = today - timedelta(days=6), today
        else:
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            if (end_date - start_date).days > MAX_CUSTOM_RANGE_DAYS:
                start_date = end_date - timedelta(days=MAX_CUSTOM_RANGE_DAYS)
    elif range_key in HISTORY_RANGE_DAYS:
        start_date = today - timedelta(days=HISTORY_RANGE_DAYS[range_key])
        end_date = today
    else:
        range_key = "week"
        start_date, end_date = today - timedelta(days=6), today

    summary = services.historical_range_summary(request.user, start_date, end_date)

    chart_data = {
        "labels": [row["date"].strftime("%d %b") for row in summary["daily_breakdown"]],
        "completed_hours": [minutes_to_hours(row["completed_minutes"]) for row in summary["daily_breakdown"]],
        "goal_hours": [minutes_to_hours(row["goal_minutes"]) for row in summary["daily_breakdown"]],
        "break_hours": [minutes_to_hours(row["break_minutes"]) for row in summary["daily_breakdown"]],
        "waste_hours": [minutes_to_hours(row["waste_minutes"]) for row in summary["daily_breakdown"]],
        "completion_percent": [row["completion_percent"] for row in summary["daily_breakdown"]],
        "missed_hours": [minutes_to_hours(row["missed_minutes"]) for row in summary["daily_breakdown"]],
        "activity_labels": [row["name"] for row in summary["activity_distribution"]],
        "activity_hours": [minutes_to_hours(row["total_minutes"]) for row in summary["activity_distribution"]],
        "activity_colors": [row["color"] for row in summary["activity_distribution"]],
    }

    return render(
        request,
        "timetracker/history.html",
        {
            "range_key": range_key,
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary,
            "chart_data": chart_data,
        },
    )


@login_required
def activity_detail(request, pk):
    activity = get_object_or_404(Activity, pk=pk, user=request.user)
    stats = services.activity_stats(request.user, activity)

    recent_sessions = TimerSession.objects.filter(
        user=request.user,
        activity=activity,
        end_at__isnull=False,
    ).select_related("subject", "topic")[:20]

    return render(
        request,
        "timetracker/activity_detail.html",
        {
            "activity": activity,
            "stats": stats,
            "recent_sessions": recent_sessions,
        },
    )


@login_required
def activity_list(request):
    activities = Activity.objects.filter(user=request.user)

    active_activities = activities.filter(is_active=True)
    archived_activities = activities.filter(is_active=False)

    edit_forms = {
        activity.pk: ActivityForm(instance=activity) for activity in activities
    }

    return render(
        request,
        "timetracker/activities.html",
        {
            "active_activities": active_activities,
            "archived_activities": archived_activities,
            "form": ActivityForm(),
            "edit_forms": edit_forms,
        },
    )


@login_required
def add_activity(request):
    if request.method == "POST":
        form = ActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = request.user
            activity.save()
            messages.success(request, "Activity created.")
        else:
            messages.error(request, "Could not create activity — check the form and try again.")

    return redirect("timetracker:activity_list")


@login_required
def edit_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, user=request.user)

    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)

        if form.is_valid():
            form.save()
            messages.success(request, "Activity updated.")

    return redirect("timetracker:activity_list")


@login_required
def archive_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, user=request.user)

    if request.method == "POST":
        activity.is_active = False
        activity.save(update_fields=["is_active"])
        messages.success(request, f"{activity.name} archived.")

    return redirect("timetracker:activity_list")


@login_required
def restore_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, user=request.user)

    if request.method == "POST":
        activity.is_active = True
        activity.save(update_fields=["is_active"])
        messages.success(request, f"{activity.name} restored.")

    return redirect("timetracker:activity_list")


@login_required
def delete_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, user=request.user)

    if request.method == "POST":
        try:
            activity.delete()
            messages.success(request, "Activity deleted.")
        except ProtectedError:
            messages.error(
                request,
                f"Can't delete {activity.name} — it already has logged sessions. Archive it instead.",
            )

    return redirect("timetracker:activity_list")


def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def _call_service(service_fn, user, *args, **kwargs):
    """Run a timer-engine service function, translating TimerStateError into a 409 JsonResponse."""
    try:
        service_fn(user, *args, **kwargs)
    except services.TimerStateError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=409)

    return JsonResponse({"ok": True, "summary": services.today_summary(user)})


@require_POST
@login_required
def start_session_view(request):
    payload = _json_body(request)

    activity_id = payload.get("activity_id")
    if not activity_id:
        return JsonResponse({"ok": False, "error": "Select an activity first."}, status=400)

    try:
        activity = Activity.objects.get(pk=activity_id, user=request.user, is_active=True)
    except Activity.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Activity not found."}, status=400)

    subject = None
    if payload.get("subject_id"):
        subject = Subject.objects.filter(pk=payload["subject_id"], user=request.user).first()

    topic = None
    if payload.get("topic_id"):
        topic = Topic.objects.filter(pk=payload["topic_id"], subject__user=request.user).first()

    notes = payload.get("notes", "")

    return _call_service(
        services.start_session, request.user, activity, subject=subject, topic=topic, notes=notes
    )


@require_POST
@login_required
def pause_session_view(request):
    return _call_service(services.pause_session, request.user)


@require_POST
@login_required
def resume_session_view(request):
    return _call_service(services.resume_session, request.user)


@require_POST
@login_required
def stop_session_view(request):
    return _call_service(services.stop_session, request.user)


@require_POST
@login_required
def start_break_view(request):
    payload = _json_body(request)
    return _call_service(
        services.start_break,
        request.user,
        reason=payload.get("reason", ""),
        planned_minutes=payload.get("planned_minutes"),
    )


@require_POST
@login_required
def end_break_view(request):
    return _call_service(services.end_break, request.user)


@require_GET
@login_required
def summary_view(request):
    return JsonResponse(services.today_summary(request.user))


@require_GET
@login_required
def timeline_data_view(request):
    events = services.today_timeline(request.user)

    data = [
        {
            "type": event.event_type,
            "occurred_at": event.occurred_at.isoformat(),
            "label": event.label,
            "duration_seconds": event.duration_seconds,
        }
        for event in events
    ]

    return JsonResponse({"events": data})
