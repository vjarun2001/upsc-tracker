from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.services import log_activity

from .models import RevisionSchedule


@login_required
def today_view(request):
    today = timezone.localdate()

    due = RevisionSchedule.objects.filter(
        user=request.user,
        is_done=False,
        scheduled_date__lte=today,
    ).select_related("topic", "topic__subject")

    upcoming = RevisionSchedule.objects.filter(
        user=request.user,
        is_done=False,
        scheduled_date__gt=today,
    ).select_related("topic", "topic__subject")[:10]

    return render(
        request,
        "revision/today.html",
        {
            "due": due,
            "upcoming": upcoming,
        },
    )


@login_required
def mark_done(request, pk):
    schedule = get_object_or_404(RevisionSchedule, pk=pk, user=request.user)

    if request.method == "POST":
        schedule.is_done = True
        schedule.save(update_fields=["is_done"])
        messages.success(request, "Revision marked complete.")

        log_activity(
            request.user,
            "revision_done",
            f"Revised topic: {schedule.topic.title} (+{schedule.stage_days}d)",
            url="/revision/",
            icon="bi-arrow-repeat",
        )

    return redirect("revision:today")
