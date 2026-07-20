from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet

from apps.mocktest.models import MockTest
from apps.planner.models import DailyTask, PomodoroSession
from apps.revision.models import RevisionSchedule
from apps.study.models import StudySession, Subject, Topic
from apps.tracker.models import Tracker, TrackerLog

from . import services


def _analytics_context(user):
    subject_labels, subject_minutes = services.minutes_per_subject(user)
    daily_labels, daily_minutes = services.daily_minutes_last_n_days(user)
    mock_labels, mock_marks, mock_accuracy = services.mock_test_trend(user)
    topic_labels, topic_percentages = services.topic_completion_per_subject(user)
    routine_labels, routine_minutes = services.routine_minutes_today(user)
    week_labels, week_minutes = services.weekly_study_minutes(user)
    week_breakdown = services.daily_study_breakdown(user)
    week_dates = list(week_breakdown.keys())
    trend_labels, trend_done, trend_pending = services.task_trend(user)
    revision_labels, revision_done, revision_overdue = services.revision_activity(user)
    confidence_counts = services.confidence_split(user)

    total_topics = Topic.objects.filter(subject__user=user).count()
    completed_topics = Topic.objects.filter(subject__user=user, status=Topic.Status.COMPLETED).count()

    return {
        "streak": services.compute_current_streak(user),
        "total_subjects": Subject.objects.filter(user=user).count(),
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "syllabus_percent": round(completed_topics / total_topics * 100) if total_topics else 0,
        "total_minutes": sum(
            s.duration_minutes for s in StudySession.objects.filter(user=user)
        )
        + sum(
            round(p.actual_duration_seconds / 60)
            for p in PomodoroSession.objects.filter(
                user=user, is_completed=True, session_type=PomodoroSession.SessionType.FOCUS
            )
        ),
        "total_mock_tests": MockTest.objects.filter(user=user).count(),
        "revision_percent": services.revision_completion_summary(user),
        "syllabus_rows": services.syllabus_progress_by_subject(user),
        "recap": services.build_daily_recap(user),
        "chart_data": {
            "subject_labels": subject_labels,
            "subject_minutes": subject_minutes,
            "daily_labels": daily_labels,
            "daily_minutes": daily_minutes,
            "week_labels": week_labels,
            "week_minutes": week_minutes,
            "week_dates": week_dates,
            "week_breakdown": week_breakdown,
            "trend_labels": trend_labels,
            "trend_done": trend_done,
            "trend_pending": trend_pending,
            "revision_labels": revision_labels,
            "revision_done": revision_done,
            "revision_overdue": revision_overdue,
            "mock_labels": mock_labels,
            "mock_marks": mock_marks,
            "mock_accuracy": mock_accuracy,
            "topic_labels": topic_labels,
            "topic_percentages": topic_percentages,
            "routine_labels": routine_labels,
            "routine_minutes": routine_minutes,
            "confidence_counts": [
                confidence_counts["not_set"],
                confidence_counts["low"],
                confidence_counts["medium"],
                confidence_counts["high"],
            ],
        },
    }


@login_required
def dashboard(request):
    today = timezone.localdate()

    context = _analytics_context(request.user)

    today_tasks = DailyTask.objects.filter(user=request.user, date=today).select_related("subject")
    tasks_done_today = today_tasks.filter(is_completed=True).count()
    tasks_total_today = today_tasks.count()

    due_revisions = RevisionSchedule.objects.filter(
        user=request.user, is_done=False, scheduled_date__lte=today
    ).select_related("topic", "topic__subject")

    habits = Tracker.objects.filter(
        user=request.user, is_active=True, kind=Tracker.Kind.BOOLEAN, category=Tracker.Category.CUSTOM
    )
    today_logs_by_tracker = {
        log.tracker_id: log
        for log in TrackerLog.objects.filter(tracker__user=request.user, date=today)
    }
    today_habit_logs = {
        tracker_id: bool(log.value) for tracker_id, log in today_logs_by_tracker.items()
    }

    health_trackers = Tracker.objects.filter(
        user=request.user, is_active=True, category=Tracker.Category.HEALTH
    )
    health_rows = [
        {"tracker": tracker, "today_log": today_logs_by_tracker.get(tracker.pk)}
        for tracker in health_trackers
    ]

    context.update(
        {
            "today_tasks": today_tasks,
            "tasks_done_today": tasks_done_today,
            "tasks_total_today": tasks_total_today,
            "due_revisions": due_revisions,
            "habits": habits,
            "today_habit_logs": today_habit_logs,
            "health_rows": health_rows,
        }
    )

    return render(request, "analytics/dashboard.html", context)


@login_required
def export_pdf(request):
    context = _analytics_context(request.user)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="upsc-tracker-report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("UPSC Aspirant Tracker — Progress Report", styles["Title"]))
    story.append(Paragraph(f"For: {request.user.email}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    summary_rows = [
        ["Metric", "Value"],
        ["Current Streak", f"{context['streak']} days"],
        ["Subjects", context["total_subjects"]],
        ["Topics", context["total_topics"]],
        ["Completed Topics", context["completed_topics"]],
        ["Total Minutes Studied", context["total_minutes"]],
        ["Mock Tests Taken", context["total_mock_tests"]],
    ]

    summary_table = Table(summary_rows, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("Minutes Studied Per Subject", styles["Heading2"]))

    subject_rows = [["Subject", "Minutes"]] + list(
        zip(
            context["chart_data"]["subject_labels"] or ["-"],
            context["chart_data"]["subject_minutes"] or [0],
        )
    )
    subject_table = Table(subject_rows, colWidths=[8 * cm, 8 * cm])
    subject_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#198754")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(subject_table)

    doc.build(story)

    return response
