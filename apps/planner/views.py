import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.activity.services import log_activity
from apps.study.models import Subject

from .forms import DailyTaskForm, PomodoroSessionLogForm
from .models import DailyTask, PomodoroSession


def _resolve_date(year, month, day):
    if year is None:
        return timezone.localdate()

    try:
        return date(year, month, day)
    except ValueError:
        raise Http404("Invalid date.")


def _day_context(request, view_date, form=None):
    tasks = DailyTask.objects.filter(
        user=request.user,
        date=view_date,
    ).select_related("subject")

    return {
        "view_date": view_date,
        "prev_date": view_date - timedelta(days=1),
        "next_date": view_date + timedelta(days=1),
        "today": timezone.localdate(),
        "tasks": tasks,
        "form": form or DailyTaskForm(user=request.user),
    }


@login_required
def day_view(request, year=None, month=None, day=None):
    view_date = _resolve_date(year, month, day)

    return render(
        request,
        "planner/day.html",
        _day_context(request, view_date),
    )


@login_required
def add_task(request):
    if request.method == "POST":

        try:
            task_date = date.fromisoformat(request.POST.get("date", ""))
        except ValueError:
            task_date = timezone.localdate()

        form = DailyTaskForm(request.POST, user=request.user)

        if form.is_valid():

            task = form.save(commit=False)

            task.user = request.user
            task.date = task_date

            next_order = (
                DailyTask.objects.filter(
                    user=request.user,
                    date=task_date,
                ).aggregate(Max("order"))["order__max"]
                or 0
            ) + 1

            task.order = next_order

            task.save()

            messages.success(request, "Task added successfully.")

            return redirect(
                "planner:day",
                year=task_date.year,
                month=task_date.month,
                day=task_date.day,
            )

        return render(
            request,
            "planner/day.html",
            _day_context(request, task_date, form=form),
        )

    return redirect("planner:day_today")


@require_POST
@login_required
def toggle_task(request, pk):
    task = get_object_or_404(DailyTask, pk=pk, user=request.user)

    task.is_completed = not task.is_completed
    task.save(update_fields=["is_completed"])

    if task.is_completed:
        log_activity(
            request.user,
            "task_completed",
            f"Completed task: {task.title}",
            url="/planner/",
            icon="bi-check-square",
        )

    return JsonResponse({"ok": True, "id": task.pk, "is_completed": task.is_completed})


@require_POST
@login_required
def delete_task(request, pk):
    task = get_object_or_404(DailyTask, pk=pk, user=request.user)
    task.delete()

    return JsonResponse({"ok": True, "id": pk})


@login_required
def pomodoro(request):
    today = timezone.localdate()

    today_tasks = DailyTask.objects.filter(user=request.user, date=today)
    subjects = Subject.objects.filter(user=request.user)

    recent_sessions = PomodoroSession.objects.filter(
        user=request.user,
        started_at__date=today,
    ).select_related("task", "subject")

    preselected_task = request.GET.get("task")
    preselected_subject = request.GET.get("subject")

    client_config = {
        "log_url": reverse("planner:log_pomodoro_session"),
        "preselected_task": preselected_task,
        "preselected_subject": preselected_subject,
    }

    return render(
        request,
        "planner/pomodoro.html",
        {
            "today_tasks": today_tasks,
            "subjects": subjects,
            "recent_sessions": recent_sessions,
            "client_config": client_config,
        },
    )


@require_POST
@login_required
def log_pomodoro_session(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": "Invalid JSON."}, status=400)

    form = PomodoroSessionLogForm(data=payload, user=request.user)

    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    session = form.save(commit=False)

    session.user = request.user
    session.completed_at = timezone.now()
    session.started_at = session.completed_at - timedelta(
        seconds=session.actual_duration_seconds
    )

    session.save()

    return JsonResponse(
        {
            "ok": True,
            "session": {
                "id": session.pk,
                "session_type": session.get_session_type_display(),
                "is_completed": session.is_completed,
                "actual_duration_seconds": session.actual_duration_seconds,
            },
        },
        status=201,
    )
