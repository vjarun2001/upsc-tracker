from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.activity.services import log_activity

from .forms import SubjectForm, TopicForm
from .models import StudySession
from .models import Subject
from .models import Topic
from .services import flatten_topics


@login_required
def dashboard(request):
    subjects = Subject.objects.filter(user=request.user).prefetch_related("topics")

    total_subjects = subjects.count()

    total_topics = Topic.objects.filter(subject__user=request.user).count()

    completed_topics = Topic.objects.filter(
        subject__user=request.user,
        status=Topic.Status.COMPLETED,
    ).count()

    sessions = StudySession.objects.filter(user=request.user)

    total_sessions = sessions.count()

    total_minutes = sum(session.duration_minutes for session in sessions)

    selected_subject = None
    topic_rows = []

    subject_id = request.GET.get("subject")

    if subject_id:
        selected_subject = subjects.filter(pk=subject_id).first()

    if not selected_subject:
        selected_subject = subjects.first()

    if selected_subject:
        topic_rows = flatten_topics(list(selected_subject.topics.all()))

    subject_edit_forms = {
        subject.pk: SubjectForm(instance=subject) for subject in subjects
    }

    return render(
        request,
        "study/dashboard.html",
        {
            "subjects": subjects,
            "total_subjects": total_subjects,
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "form": SubjectForm(),
            "topic_form": TopicForm(user=request.user),
            "selected_subject": selected_subject,
            "topic_rows": topic_rows,
            "topic_statuses": Topic.Status.choices,
            "topic_confidences": Topic.Confidence.choices,
            "subject_edit_forms": subject_edit_forms,
        },
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

            return redirect(f"{reverse('study:dashboard')}?subject={subject.pk}")

    return redirect("study:dashboard")


@login_required
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated.")

    return redirect(f"{reverse('study:dashboard')}?subject={subject.pk}")


@login_required
def add_topic(request):

    if request.method == "POST":

        form = TopicForm(request.POST, user=request.user)

        if form.is_valid():

            topic = form.save()

            messages.success(request, "Topic added successfully.")

            return redirect(f"{reverse('study:dashboard')}?subject={topic.subject_id}")

    return redirect("study:dashboard")


@login_required
def update_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk, subject__user=request.user)

    if request.method == "POST":

        status = request.POST.get("status")
        confidence = request.POST.get("confidence")
        weightage = request.POST.get("weightage")

        update_fields = []

        if status and status in Topic.Status.values:
            was_completed = topic.status == Topic.Status.COMPLETED
            topic.status = status
            update_fields.append("status")

            if status == Topic.Status.COMPLETED and not was_completed:
                log_activity(
                    request.user,
                    "topic_completed",
                    f"Completed topic: {topic.title}",
                    url="/study/",
                    icon="bi-check-circle",
                )

        if confidence is not None and (confidence in Topic.Confidence.values or confidence == ""):
            topic.confidence = confidence
            update_fields.append("confidence")

        if weightage:
            try:
                topic.weightage = max(1, int(weightage))
                update_fields.append("weightage")
            except ValueError:
                pass

        if update_fields:
            topic.save(update_fields=update_fields)

        next_url = request.POST.get("next")

        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

    return redirect(f"{reverse('study:dashboard')}?subject={topic.subject_id}")
