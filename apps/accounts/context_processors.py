from .services import today_seconds


def session_status(request):
    if not request.user.is_authenticated:
        return {"today_seconds": 0}

    return {"today_seconds": today_seconds(request.user)}
