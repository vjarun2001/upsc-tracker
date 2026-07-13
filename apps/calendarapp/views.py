from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from apps.planner.forms import DailyTaskForm

from . import services


def _resolve_date(year, month, day):
    if year is None:
        return timezone.localdate()

    try:
        return date(year, month, day)
    except ValueError:
        raise Http404("Invalid date.")


@login_required
def day_view(request, year=None, month=None, day=None):
    view_date = _resolve_date(year, month, day)

    events_by_date = services.get_events_by_date(request.user, view_date, view_date)
    all_day, hours = services.build_day_hours(events_by_date.get(view_date, []))

    return render(
        request,
        "calendarapp/day.html",
        {
            "view_date": view_date,
            "prev_date": view_date - timedelta(days=1),
            "next_date": view_date + timedelta(days=1),
            "today": timezone.localdate(),
            "all_day_events": all_day,
            "hours": hours,
            "task_form": DailyTaskForm(user=request.user),
        },
    )


@login_required
def week_view(request, year=None, month=None, day=None):
    anchor = _resolve_date(year, month, day)
    monday = anchor - timedelta(days=anchor.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    events_by_date = services.get_events_by_date(request.user, days[0], days[-1])

    week_days = [{"date": d, "events": events_by_date.get(d, [])} for d in days]

    return render(
        request,
        "calendarapp/week.html",
        {
            "week_days": week_days,
            "week_start": days[0],
            "week_end": days[-1],
            "prev_week": monday - timedelta(days=7),
            "next_week": monday + timedelta(days=7),
            "today": timezone.localdate(),
        },
    )


@login_required
def month_view(request, year=None, month=None):
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    first_day = date(year, month, 1)
    last_day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)

    events_by_date = services.get_events_by_date(request.user, first_day, last_day)
    weeks = services.build_month_grid(year, month, events_by_date)

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1))

    return render(
        request,
        "calendarapp/month.html",
        {
            "weeks": weeks,
            "month_date": first_day,
            "prev_month": prev_month,
            "next_month": next_month,
            "today": today,
        },
    )
