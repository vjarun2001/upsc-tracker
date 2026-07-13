from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.services import log_activity
from apps.study.models import Topic

from .models import RevisionSchedule
from .services import MAX_STAGE, advance_revision


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

    total_topics = Topic.objects.filter(subject__user=request.user).count()

    stage_rings = []
    total_done = 0

    for stage in range(1, MAX_STAGE + 1):
        done = RevisionSchedule.objects.filter(
            user=request.user, stage=stage, is_done=True
        ).count()
        total_done += done
        stage_rings.append(
            {
                "stage": stage,
                "done": done,
                "total": total_topics,
                "percent": round(done / total_topics * 100) if total_topics else 0,
            }
        )

    return render(
        request,
        "revision/today.html",
        {
            "due": due,
            "upcoming": upcoming,
            "total_topics": total_topics,
            "total_done": total_done,
            "total_percent": round(total_done / total_topics * 100) if total_topics else 0,
            "stage_rings": stage_rings,
            "confidence_choices": RevisionSchedule.Confidence.choices,
        },
    )


@login_required
def mark_done(request, pk):
    schedule = get_object_or_404(RevisionSchedule, pk=pk, user=request.user)

    if request.method == "POST":
        confidence = request.POST.get("confidence") or RevisionSchedule.Confidence.MEDIUM

        advance_revision(schedule, confidence)

        messages.success(request, "Revision marked complete.")

        log_activity(
            request.user,
            "revision_done",
            f"Revised topic: {schedule.topic.title} (R{schedule.stage})",
            url="/revision/",
            icon="bi-arrow-repeat",
        )

    return redirect("revision:today")
