def format_minutes_hm(total_minutes):
    """Render a minutes count as "Xh Ym", e.g. 225 -> "3h 45m"."""
    try:
        total_minutes = int(round(total_minutes))
    except (TypeError, ValueError):
        return total_minutes

    hours, minutes = divmod(max(total_minutes, 0), 60)
    return f"{hours}h {minutes}m"


def format_seconds_hm(total_seconds):
    return format_minutes_hm((total_seconds or 0) / 60)


def minutes_to_hours(total_minutes, ndigits=1):
    """Decimal hours for chart axes, e.g. 90 -> 1.5."""
    try:
        return round(int(total_minutes) / 60, ndigits)
    except (TypeError, ValueError):
        return 0
