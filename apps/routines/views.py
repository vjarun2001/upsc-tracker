from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.services import log_activity

from .forms import RoutineForm, RoutineLogForm
from .models import Routine


@login_required
def list_routines(request):
    routines = Routine.objects.filter(user=request.user, is_active=True)

    return render(
        request,
        "routines/list.html",
        {
            "routines": routines,
            "form": RoutineForm(),
            "log_form": RoutineLogForm(),
        },
    )


@login_required
def add_routine(request):
    if request.method == "POST":
        form = RoutineForm(request.POST)

        if form.is_valid():
            routine = form.save(commit=False)
            routine.user = request.user
            routine.save()
            messages.success(request, "Routine added.")

    return redirect("routines:list")


@login_required
def delete_routine(request, pk):
    routine = get_object_or_404(Routine, pk=pk, user=request.user)

    if request.method == "POST":
        routine.delete()
        messages.success(request, "Routine deleted.")

    return redirect("routines:list")


@login_required
def log_routine(request, pk):
    routine = get_object_or_404(Routine, pk=pk, user=request.user)

    if request.method == "POST":
        today = timezone.localdate()
        instance = routine.logs.filter(date=today).first()

        form = RoutineLogForm(request.POST, instance=instance)

        if form.is_valid():
            log = form.save(commit=False)
            log.routine = routine
            log.date = today
            log.save()

            log_activity(
                request.user,
                "routine",
                f"Logged routine '{routine.name}': {log.minutes_spent} min",
                url="/routines/",
                icon="bi-arrow-repeat",
            )

            messages.success(request, "Routine logged.")

    return redirect("routines:list")
