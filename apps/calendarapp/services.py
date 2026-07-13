from datetime import timedelta


def get_events_by_date(user, start_date, end_date):
    from apps.mocktest.models import MockTest
    from apps.planner.models import DailyTask
    from apps.revision.models import RevisionSchedule

    events = {}

    tasks = DailyTask.objects.filter(
        user=user, date__gte=start_date, date__lte=end_date
    ).select_related("subject", "tracker")

    for task in tasks:
        title = task.title
        if task.tracker_id:
            title = f"{title} ({task.tracker.name})" if title != task.tracker.name else title

        events.setdefault(task.date, []).append(
            {
                "kind": "task",
                "title": title,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "color": "#6f42c1" if task.tracker_id else (task.subject.color if task.subject else "#f0635a"),
                "is_completed": task.is_completed,
            }
        )

    revisions = RevisionSchedule.objects.filter(
        user=user,
        scheduled_date__gte=start_date,
        scheduled_date__lte=end_date,
        is_done=False,
    ).select_related("topic")

    for revision in revisions:
        events.setdefault(revision.scheduled_date, []).append(
            {
                "kind": "revision",
                "title": f"Revise: {revision.topic.title}",
                "start_time": None,
                "end_time": None,
                "color": "#fd7e14",
                "is_completed": False,
            }
        )

    mock_tests = MockTest.objects.filter(
        user=user, test_date__gte=start_date, test_date__lte=end_date
    )

    for test in mock_tests:
        events.setdefault(test.test_date, []).append(
            {
                "kind": "mocktest",
                "title": test.name,
                "start_time": None,
                "end_time": None,
                "color": "#6f42c1",
                "is_completed": False,
            }
        )

    for day_events in events.values():
        day_events.sort(key=lambda e: (e["start_time"] is None, e["start_time"] or "00:00"))

    return events


def build_day_hours(events_for_day):
    all_day = [e for e in events_for_day if not e["start_time"]]
    timed = [e for e in events_for_day if e["start_time"]]

    hours = []
    for hour in range(24):
        hour_events = [e for e in timed if e["start_time"].hour == hour]
        hours.append({"hour": hour, "events": hour_events})

    return all_day, hours


def build_month_grid(year, month, events_by_date):
    import calendar as stdlib_calendar
    from datetime import date

    cal = stdlib_calendar.Calendar(firstweekday=0)
    weeks = []

    for week in cal.monthdatescalendar(year, month):
        week_rows = []
        for day in week:
            week_rows.append(
                {
                    "date": day,
                    "in_month": day.month == month,
                    "events": events_by_date.get(day, []),
                }
            )
        weeks.append(week_rows)

    return weeks
