from .services import get_notifications


def notifications(request):
    if not request.user.is_authenticated:
        return {"notifications": [], "notifications_count": 0}

    items = get_notifications(request.user)

    return {"notifications": items, "notifications_count": len(items)}
