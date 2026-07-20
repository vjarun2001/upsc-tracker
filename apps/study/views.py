from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.activity.services import log_activity

from .forms import SubjectForm, TopicForm
from .models import StudySession
from .models import Subject
from .models import Topic
from .services import descendant_ids, flatten_topics, time_of_day_bucket


def _time_spent_per_topic(user, topics):
    from apps.planner.models import PomodoroSession

    minutes = {topic.pk: 0 for topic in topics}

    for session in StudySession.objects.filter(user=user, topic__in=topics):
        minutes[session.topic_id] = minutes.get(session.topic_id, 0) + session.duration_minutes

    focus_sessions = PomodoroSession.objects.filter(
        user=user,
        is_completed=True,
        session_type=PomodoroSession.SessionType.FOCUS,
        topic__in=topics,
    )
    for session in focus_sessions:
        minutes[session.topic_id] = minutes.get(session.topic_id, 0) + round(
            session.actual_duration_seconds / 60
        )

    return minutes


@login_required
def dashboard(request):
    subjects = Subject.objects.filter(user=request.user).prefetch_related("topics")

    total_subjects = subjects.count()

    total_topics = Topic.objects.filter(subject__user=request.user).count()

    completed_topics = Topic.objects.filter(
        subject__user=request.user,
        status=Topic.Status.COMPLETED,
    ).count()

    from apps.planner.models import PomodoroSession

    sessions = StudySession.objects.filter(user=request.user)

    focus_sessions = PomodoroSession.objects.filter(
        user=request.user,
        is_completed=True,
        session_type=PomodoroSession.SessionType.FOCUS,
    )

    total_sessions = sessions.count() + focus_sessions.count()

    total_minutes = sum(session.duration_minutes for session in sessions) + sum(
        round(session.actual_duration_seconds / 60) for session in focus_sessions
    )

    selected_subject = None
    topic_rows = []

    subject_id = request.GET.get("subject")

    if subject_id:
        selected_subject = subjects.filter(pk=subject_id).first()

    if not selected_subject:
        selected_subject = subjects.first()

    move_targets = {}
    topic_minutes = {}

    if selected_subject:
        all_subject_topics = list(selected_subject.topics.all())
        topic_rows = flatten_topics(all_subject_topics)

        for topic, _depth in topic_rows:
            forbidden = descendant_ids(topic, all_subject_topics) | {topic.pk}
            move_targets[topic.pk] = [
                (other.pk, "—" * depth + " " + other.title)
                for other, depth in topic_rows
                if other.pk not in forbidden
            ]

        topic_minutes = _time_spent_per_topic(request.user, all_subject_topics)

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
            "move_targets": move_targets,
            "topic_minutes": topic_minutes,
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
                topic.completed_at = timezone.now()
                update_fields.append("completed_at")

                log_activity(
                    request.user,
                    "topic_completed",
                    f"Completed topic: {topic.title}",
                    url="/study/",
                    icon="bi-check-circle",
                )
            elif status != Topic.Status.COMPLETED and was_completed:
                topic.completed_at = None
                update_fields.append("completed_at")

                from apps.revision.models import RevisionSchedule

                RevisionSchedule.objects.filter(topic=topic).delete()

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


@login_required
def move_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk, subject__user=request.user)

    if request.method == "POST":
        direction = request.POST.get("direction")

        siblings = list(
            Topic.objects.filter(
                subject=topic.subject, parent_id=topic.parent_id
            ).order_by("order", "id")
        )
        index = next((i for i, t in enumerate(siblings) if t.pk == topic.pk), None)

        if index is not None:
            if direction == "up":
                swap_index = index - 1
            elif direction == "down":
                swap_index = index + 1
            else:
                swap_index = None

            if swap_index is not None and 0 <= swap_index < len(siblings):
                siblings[index], siblings[swap_index] = siblings[swap_index], siblings[index]
                for position, sibling in enumerate(siblings):
                    sibling.order = position
                Topic.objects.bulk_update(siblings, ["order"])

        next_url = request.POST.get("next")

        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

    return redirect(f"{reverse('study:dashboard')}?subject={topic.subject_id}")


@login_required
def reparent_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk, subject__user=request.user)

    if request.method == "POST":
        new_parent_id = request.POST.get("parent") or None
        all_topics = list(Topic.objects.filter(subject=topic.subject))
        forbidden = descendant_ids(topic, all_topics) | {topic.pk}

        if new_parent_id and int(new_parent_id) in forbidden:
            messages.error(request, "Can't move a topic under itself or one of its own subtopics.")
        else:
            topic.parent_id = int(new_parent_id) if new_parent_id else None

            max_order = Topic.objects.filter(
                subject=topic.subject, parent_id=topic.parent_id
            ).exclude(pk=topic.pk).aggregate(Max("order"))["order__max"] or 0

            topic.order = max_order + 1
            topic.save(update_fields=["parent", "order"])
            messages.success(request, "Topic moved.")

        next_url = request.POST.get("next")

        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

    return redirect(f"{reverse('study:dashboard')}?subject={topic.subject_id}")


@login_required
def topic_time_log(request, pk):
    from apps.planner.models import PomodoroSession

    topic = get_object_or_404(Topic, pk=pk, subject__user=request.user)

    entries = []

    for session in StudySession.objects.filter(user=request.user, topic=topic):
        entries.append(
            {
                "date": session.start_time.date(),
                "start_time": timezone.localtime(session.start_time).time(),
                "end_time": timezone.localtime(session.end_time).time(),
                "duration_minutes": session.duration_minutes,
                "source": "Manual Log",
            }
        )

    focus_sessions = PomodoroSession.objects.filter(
        user=request.user,
        is_completed=True,
        session_type=PomodoroSession.SessionType.FOCUS,
        topic=topic,
    )

    for session in focus_sessions:
        started = timezone.localtime(session.started_at)
        completed = timezone.localtime(session.completed_at)
        entries.append(
            {
                "date": started.date(),
                "start_time": started.time(),
                "end_time": completed.time(),
                "duration_minutes": round(session.actual_duration_seconds / 60),
                "source": "Focus Timer",
            }
        )

    for entry in entries:
        entry["bucket"] = time_of_day_bucket(entry["start_time"])

    entries.sort(key=lambda e: (e["date"], e["start_time"]), reverse=True)

    period = request.GET.get("period", "all")
    if period in ("morning", "afternoon", "evening", "night"):
        filtered_entries = [e for e in entries if e["bucket"] == period]
    else:
        period = "all"
        filtered_entries = entries

    bucket_totals = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
    for entry in entries:
        bucket_totals[entry["bucket"]] += entry["duration_minutes"]

    total_minutes = sum(e["duration_minutes"] for e in filtered_entries)

    return render(
        request,
        "study/topic_log.html",
        {
            "topic": topic,
            "entries": filtered_entries,
            "total_minutes": total_minutes,
            "total_sessions": len(filtered_entries),
            "bucket_totals": bucket_totals,
            "period": period,
        },
    )
