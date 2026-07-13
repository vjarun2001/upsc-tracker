from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.activity.services import log_activity

from .forms import GoalForm, MilestoneForm
from .models import Goal, Milestone


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user).prefetch_related("milestones")

    goal_edit_forms = {
        goal.pk: GoalForm(instance=goal, user=request.user) for goal in goals
    }

    return render(
        request,
        "goals/list.html",
        {
            "goals": goals,
            "completed_count": goals.filter(is_completed=True).count(),
            "form": GoalForm(user=request.user),
            "goal_edit_forms": goal_edit_forms,
            "milestone_form": MilestoneForm(),
        },
    )


@login_required
def add_goal(request):
    if request.method == "POST":
        form = GoalForm(request.POST, user=request.user)

        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Goal added.")
            return redirect("goals:list")

    return redirect("goals:list")


@login_required
def edit_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == "POST":
        form = GoalForm(request.POST, instance=goal, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Goal updated.")

    return redirect("goals:list")


@login_required
def toggle_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == "POST":
        goal.is_completed = not goal.is_completed
        goal.save(update_fields=["is_completed"])

        if goal.is_completed:
            log_activity(
                request.user,
                "goal_completed",
                f"Completed goal: {goal.title}",
                url="/goals/",
                icon="bi-bullseye",
            )

    return redirect("goals:list")


@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == "POST":
        goal.delete()
        messages.success(request, "Goal deleted.")

    return redirect("goals:list")


@login_required
def add_milestone(request, goal_pk):
    goal = get_object_or_404(Goal, pk=goal_pk, user=request.user)

    if request.method == "POST":
        form = MilestoneForm(request.POST)

        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.goal = goal
            milestone.order = goal.milestones.count() + 1
            milestone.save()

    return redirect("goals:list")


@login_required
def toggle_milestone(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk, goal__user=request.user)

    if request.method == "POST":
        milestone.is_completed = not milestone.is_completed
        milestone.save(update_fields=["is_completed"])

        if milestone.is_completed:
            log_activity(
                request.user,
                "milestone_completed",
                f"Completed milestone: {milestone.title}",
                url="/goals/",
                icon="bi-flag",
            )

    return redirect("goals:list")
