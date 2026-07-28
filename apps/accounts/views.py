from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.models import ExamProfile

from .forms import DailyUnsleptHoursForm
from .forms import ExamProfileForm
from .forms import ProfileForm
from .forms import UserForm
from .models import LoginSession
from .services import hours_collected_today, today_seconds



@login_required
def profile(request):

    exam_profile, _ = ExamProfile.objects.get_or_create(user=request.user)

    if request.method == "POST" and "save_profile" in request.POST:

        user_form = UserForm(
            request.POST,
            instance=request.user,
        )

        profile_form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile,
        )

        exam_form = ExamProfileForm(instance=exam_profile)

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Profile updated successfully.",
            )

            return redirect("accounts:profile")

    elif request.method == "POST" and "save_exam_dates" in request.POST:

        user_form = UserForm(instance=request.user)

        profile_form = ProfileForm(instance=request.user.profile)

        exam_form = ExamProfileForm(
            request.POST,
            instance=exam_profile,
        )

        if exam_form.is_valid():

            exam_form.save()

            messages.success(
                request,
                "Exam dates updated successfully.",
            )

            return redirect("accounts:profile")

    else:

        user_form = UserForm(instance=request.user)

        profile_form = ProfileForm(instance=request.user.profile)

        exam_form = ExamProfileForm(instance=exam_profile)

    return render(
        request,
        "account/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "exam_form": exam_form,
        },
    )


@login_required
def daily_unslept_hours(request):
    if hours_collected_today(request.user):
        return redirect("analytics:dashboard")

    session = (
        LoginSession.objects.filter(user=request.user, logout_at__isnull=True)
        .order_by("-login_at")
        .first()
    )

    if request.method == "POST":
        form = DailyUnsleptHoursForm(request.POST)

        if form.is_valid():
            from apps.timetracker.services import get_or_open_daily_timer

            goal_minutes = form.cleaned_data["hours"] * 60

            request.user.profile.daily_study_target_minutes = goal_minutes
            request.user.profile.save(update_fields=["daily_study_target_minutes"])

            # This prompt is specifically about *today* — sync today's DailyTimer directly
            # too, not just the profile default, in case it already existed (e.g. someone
            # touched the Timer before submitting today's hours).
            daily_timer = get_or_open_daily_timer(request.user)
            daily_timer.goal_minutes = goal_minutes
            daily_timer.save(update_fields=["goal_minutes"])

            if session:
                session.hours_collected = True
                session.save(update_fields=["hours_collected"])

            return redirect("analytics:dashboard")
    else:
        form = DailyUnsleptHoursForm()

    return render(request, "account/daily_hours.html", {"form": form})


@require_POST
@login_required
def heartbeat(request):
    session = (
        LoginSession.objects.filter(user=request.user, logout_at__isnull=True)
        .order_by("-login_at")
        .first()
    )

    if session:
        session.last_seen_at = timezone.now()
        session.save(update_fields=["last_seen_at"])

    return JsonResponse({"today_seconds": today_seconds(request.user)})
