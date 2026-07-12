from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.services import log_activity

from .forms import HabitForm, SleepLogForm, WaterLogForm
from .models import Habit, HabitLog, MealLog, SleepLog, WaterLog


@login_required
def dashboard(request):
    today = timezone.localdate()

    sleep_log = SleepLog.objects.filter(user=request.user, date=today).first()
    water_log = WaterLog.objects.filter(user=request.user, date=today).first()

    habits = Habit.objects.filter(user=request.user, is_active=True)

    today_habit_logs = {
        log.habit_id: log.is_done
        for log in HabitLog.objects.filter(habit__user=request.user, date=today)
    }

    meal_logs = {
        log.meal_type: log
        for log in MealLog.objects.filter(user=request.user, date=today)
    }

    meals = [
        {
            "type": choice.value,
            "label": choice.label,
            "log": meal_logs.get(choice.value),
        }
        for choice in MealLog.MealType
    ]

    return render(
        request,
        "wellness/dashboard.html",
        {
            "sleep_log": sleep_log,
            "water_log": water_log,
            "sleep_form": SleepLogForm(instance=sleep_log),
            "water_form": WaterLogForm(instance=water_log or WaterLog(glasses=0, target=8)),
            "habit_form": HabitForm(),
            "habits": habits,
            "today_habit_logs": today_habit_logs,
            "meals": meals,
        },
    )


@login_required
def log_sleep(request):
    if request.method == "POST":
        today = timezone.localdate()

        instance = SleepLog.objects.filter(user=request.user, date=today).first()
        form = SleepLogForm(request.POST, instance=instance)

        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.date = today
            log.save()
            messages.success(request, "Sleep logged.")

    return redirect("wellness:dashboard")


@login_required
def log_water(request):
    if request.method == "POST":
        today = timezone.localdate()

        instance = WaterLog.objects.filter(user=request.user, date=today).first()
        form = WaterLogForm(request.POST, instance=instance)

        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.date = today
            log.save()
            messages.success(request, "Water intake logged.")

    return redirect("wellness:dashboard")


@login_required
def add_habit(request):
    if request.method == "POST":
        form = HabitForm(request.POST)

        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, "Habit added.")

    return redirect("wellness:dashboard")


@login_required
def toggle_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    if request.method == "POST":
        today = timezone.localdate()

        log, _ = HabitLog.objects.get_or_create(habit=habit, date=today)
        log.is_done = not log.is_done
        log.save(update_fields=["is_done"])

        if log.is_done:
            log_activity(
                request.user,
                "habit",
                f"Completed habit: {habit.name}",
                url="/wellness/",
                icon="bi-check2-circle",
            )

    return redirect("wellness:dashboard")


@login_required
def toggle_meal(request, meal_type):
    if request.method == "POST":
        today = timezone.localdate()

        log, _ = MealLog.objects.get_or_create(
            user=request.user, date=today, meal_type=meal_type
        )
        log.eaten = not log.eaten
        log.eaten_at = timezone.localtime().time() if log.eaten else None
        log.save(update_fields=["eaten", "eaten_at"])

        if log.eaten:
            log_activity(
                request.user,
                "meal",
                f"Ate {log.get_meal_type_display()}",
                url="/wellness/",
                icon="bi-cup-hot",
            )

    return redirect("wellness:dashboard")
