from datetime import timedelta

from django.utils import timezone

from .models import Tracker


def heatmap_cells(tracker, weeks=12):
    today = timezone.localdate()

    end = today
    start = end - timedelta(weeks=weeks) + timedelta(days=1)
    start -= timedelta(days=start.weekday())

    logs = {log.date: log.value for log in tracker.logs.filter(date__gte=start, date__lte=end)}

    cells = []
    current = start

    while current <= end:
        value = logs.get(current, 0)

        if tracker.kind == Tracker.Kind.BOOLEAN:
            level = 3 if value > 0 else 0
        else:
            ratio = value / tracker.target_value if tracker.target_value else 0
            if ratio <= 0:
                level = 0
            elif ratio < 0.5:
                level = 1
            elif ratio < 1:
                level = 2
            else:
                level = 3

        cells.append(
            {
                "date": current,
                "level": level,
                "value": value,
                "is_today": current == today,
            }
        )

        current += timedelta(days=1)

    return cells
