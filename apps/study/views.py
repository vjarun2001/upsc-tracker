from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render

from apps.activity.services import log_activity

from .forms import SubjectForm, TopicForm
from .models import StudySession
from .models import Subject
from .models import Topic


def _dashboard_context(request, subject_form=None, topic_form=None):
    subjects = Subject.objects.filter(user=request.user).prefetch_related("topics")

    total_subjects = subjects.count()

    total_topics = Topic.objects.filter(
        subject__user=request.user
    ).count()

    completed_topics = Topic.objects.filter(
        subject__user=request.user,
        is_completed=True,
    ).count()

    sessions = StudySession.objects.filter(
        user=request.user
    )

    total_sessions = sessions.count()

    total_minutes = sum(
        session.duration_minutes
        for session in sessions
    )

    return {
        "subjects": subjects,
        "total_subjects": total_subjects,
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "form": subject_form or SubjectForm(),
        "topic_form": topic_form or TopicForm(user=request.user),
    }


@login_required
def dashboard(request):
    return render(
        request,
        "study/dashboard.html",
        _dashboard_context(request),
    )


@login_required
def add_subject(request):

    if request.method == "POST":

        form = SubjectForm(request.POST)

        if form.is_valid():

            subject = form.save(commit=False)

            subject.user = request.user

            subject.save()

            messages.success(
                request,
                "Subject created successfully.",
            )

            return redirect("study:dashboard")

        return render(
            request,
            "study/dashboard.html",
            _dashboard_context(request, subject_form=form),
        )

    return redirect("study:dashboard")


@login_required
def add_topic(request):

    if request.method == "POST":

        form = TopicForm(request.POST, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, "Topic added successfully.")

            return redirect("study:dashboard")

        return render(
            request,
            "study/dashboard.html",
            _dashboard_context(request, topic_form=form),
        )

    return redirect("study:dashboard")


@login_required
def toggle_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk, subject__user=request.user)

    if request.method == "POST":
        topic.is_completed = not topic.is_completed
        topic.save(update_fields=["is_completed"])

        if topic.is_completed:
            log_activity(
                request.user,
                "topic_completed",
                f"Completed topic: {topic.title}",
                url="/study/",
                icon="bi-check-circle",
            )

    return redirect("study:dashboard")
