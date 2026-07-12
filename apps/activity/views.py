from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_today_activity


@login_required
def today_view(request):
    return render(
        request,
        "activity/today.html",
        {"activities": get_today_activity(request.user)},
    )
