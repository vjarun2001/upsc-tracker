from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
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
from apps.study.models import StudySession, Subject, Topic

from . import services


def _analytics_context(user):
    subject_labels, subject_minutes = services.minutes_per_subject(user)
    daily_labels, daily_minutes = services.daily_minutes_last_n_days(user)
    mock_labels, mock_marks, mock_accuracy = services.mock_test_trend(user)
    topic_labels, topic_percentages = services.topic_completion_per_subject(user)
    routine_labels, routine_minutes = services.routine_minutes_today(user)

    return {
        "streak": services.compute_current_streak(user),
        "total_subjects": Subject.objects.filter(user=user).count(),
        "total_topics": Topic.objects.filter(subject__user=user).count(),
        "completed_topics": Topic.objects.filter(subject__user=user, is_completed=True).count(),
        "total_minutes": sum(
            s.duration_minutes for s in StudySession.objects.filter(user=user)
        ),
        "total_mock_tests": MockTest.objects.filter(user=user).count(),
        "recap": services.build_daily_recap(user),
        "chart_data": {
            "subject_labels": subject_labels,
            "subject_minutes": subject_minutes,
            "daily_labels": daily_labels,
            "daily_minutes": daily_minutes,
            "mock_labels": mock_labels,
            "mock_marks": mock_marks,
            "mock_accuracy": mock_accuracy,
            "topic_labels": topic_labels,
            "topic_percentages": topic_percentages,
            "routine_labels": routine_labels,
            "routine_minutes": routine_minutes,
        },
    }


@login_required
def dashboard(request):
    return render(request, "analytics/dashboard.html", _analytics_context(request.user))


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
