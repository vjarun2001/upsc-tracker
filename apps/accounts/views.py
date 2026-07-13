from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.models import ExamProfile

from .forms import ExamProfileForm
from .forms import ProfileForm
from .forms import UserForm
from .models import LoginSession
from .services import today_seconds


@login_required
def profile(request):

    exam_profile, _ = ExamProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        user_form = UserForm(
            request.POST,
            instance=request.user,
        )

        profile_form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile,
        )

        exam_form = ExamProfileForm(
            request.POST,
            instance=exam_profile,
        )

        if user_form.is_valid() and profile_form.is_valid() and exam_form.is_valid():

            user_form.save()
            profile_form.save()
            exam_form.save()

            messages.success(
                request,
                "Profile updated successfully.",
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
