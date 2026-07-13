from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.common.choices import Phase

from . import services
from .forms import MockTestForm, TestGoalForm
from .models import MockTest, TestGoal


@login_required
def test_list(request):
    active_phase = request.GET.get("phase") or Phase.PRELIMS.value

    tests = MockTest.objects.filter(user=request.user, phase=active_phase).select_related("subject")

    goal, _ = TestGoal.objects.get_or_create(user=request.user)

    labels, scores, accuracy = services.score_and_accuracy_trend(request.user, phase=active_phase)
    stats = services.summary_stats(request.user, phase=active_phase)

    test_edit_forms = {
        test.pk: MockTestForm(instance=test, user=request.user) for test in tests
    }

    return render(
        request,
        "mocktest/list.html",
        {
            "tests": tests,
            "form": MockTestForm(user=request.user),
            "test_edit_forms": test_edit_forms,
            "goal_form": TestGoalForm(instance=goal),
            "goal": goal,
            "active_phase": active_phase,
            "stats": stats,
            "chart_data": {
                "labels": labels,
                "scores": scores,
                "accuracy": accuracy,
            },
        },
    )


@login_required
def add_test(request):
    if request.method == "POST":
        form = MockTestForm(request.POST, user=request.user)

        if form.is_valid():
            test = form.save(commit=False)
            test.user = request.user
            test.save()
            messages.success(request, "Mock test added.")

    return redirect("mocktest:list")


@login_required
def edit_test(request, pk):
    test = get_object_or_404(MockTest, pk=pk, user=request.user)

    if request.method == "POST":
        form = MockTestForm(request.POST, instance=test, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Mock test updated.")

    return redirect("mocktest:list")


@login_required
def delete_test(request, pk):
    test = get_object_or_404(MockTest, pk=pk, user=request.user)

    if request.method == "POST":
        test.delete()
        messages.success(request, "Mock test deleted.")

    return redirect("mocktest:list")


@login_required
def set_goal(request):
    goal, _ = TestGoal.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = TestGoalForm(request.POST, instance=goal)

        if form.is_valid():
            form.save()
            messages.success(request, "Goal updated.")

    return redirect("mocktest:list")
