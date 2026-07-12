from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MockTestForm
from .models import MockTest


@login_required
def test_list(request):
    tests = MockTest.objects.filter(user=request.user).select_related("subject")

    return render(
        request,
        "mocktest/list.html",
        {
            "tests": tests,
            "form": MockTestForm(user=request.user),
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

        tests = MockTest.objects.filter(user=request.user).select_related("subject")
        return render(request, "mocktest/list.html", {"tests": tests, "form": form})

    return redirect("mocktest:list")


@login_required
def delete_test(request, pk):
    test = get_object_or_404(MockTest, pk=pk, user=request.user)

    if request.method == "POST":
        test.delete()
        messages.success(request, "Mock test deleted.")

    return redirect("mocktest:list")
