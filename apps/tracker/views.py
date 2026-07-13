from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.services import log_activity

from . import services
from .forms import TrackerForm
from .models import Tracker

RANGE_WEEKS = {"7d": 1, "30d": 5, "1y": 52}

HEATMAP_COLORS = ["#6f42c1", "#20c997", "#0d6efd", "#fd7e14", "#dc3545", "#198754"]


@login_required
def dashboard(request):
    trackers = Tracker.objects.filter(user=request.user, is_active=True)

    date_range = request.GET.get("range", "30d")
    weeks = RANGE_WEEKS.get(date_range, 5)

    rows = []
    best_streak = 0
    best_streak_tracker = None
    completion_total = 0

    for index, tracker in enumerate(trackers):
        streak = tracker.current_streak()
        avg = tracker.avg_completion_percent()

        if streak > best_streak:
            best_streak = streak
            best_streak_tracker = tracker.name

        completion_total += avg

        rows.append(
            {
                "tracker": tracker,
                "today_log": tracker.today_log(),
                "streak": streak,
                "avg": avg,
                "cells": services.heatmap_cells(tracker, weeks=weeks),
                "color": HEATMAP_COLORS[index % len(HEATMAP_COLORS)],
                "edit_form": TrackerForm(instance=tracker),
            }
        )

    avg_completion = round(completion_total / len(rows)) if rows else 0

    return render(
        request,
        "tracker/dashboard.html",
        {
            "rows": rows,
            "form": TrackerForm(),
            "avg_completion": avg_completion,
            "best_streak": best_streak,
            "best_streak_tracker": best_streak_tracker,
            "date_range": date_range,
        },
    )


@login_required
def add_tracker(request):
    if request.method == "POST":
        form = TrackerForm(request.POST)

        if form.is_valid():
            tracker = form.save(commit=False)
            tracker.user = request.user
            tracker.save()
            messages.success(request, "Tracker created.")

    return redirect("tracker:dashboard")


@login_required
def edit_tracker(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk, user=request.user)

    if request.method == "POST":
        form = TrackerForm(request.POST, instance=tracker)

        if form.is_valid():
            form.save()
            messages.success(request, "Tracker updated.")

    return redirect("tracker:dashboard")


@login_required
def delete_tracker(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk, user=request.user)

    if request.method == "POST":
        tracker.delete()
        messages.success(request, "Tracker deleted.")

    return redirect("tracker:dashboard")


@login_required
def log_tracker(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk, user=request.user)

    if request.method == "POST":
        today = timezone.localdate()

        log, _ = tracker.logs.get_or_create(date=today)

        if tracker.kind == Tracker.Kind.BOOLEAN:
            if log.value:
                return redirect("tracker:dashboard")
            log.value = 1
        else:
            try:
                log.value = max(0, int(request.POST.get("value", log.value)))
            except ValueError:
                pass

        log.logged_time = timezone.localtime().time()
        log.save(update_fields=["value", "logged_time"])

        if log.value > 0:
            log_activity(
                request.user,
                "tracker",
                f"Logged {tracker.name}: {log.value}",
                url="/tracker/",
                icon=tracker.icon,
            )

    return redirect("tracker:dashboard")
