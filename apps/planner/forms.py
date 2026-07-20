from django import forms

from apps.study.models import Subject, Topic
from apps.tracker.models import Tracker

from .models import DailyTask, PomodoroSession


class DailyTaskForm(forms.ModelForm):
    class Meta:
        model = DailyTask

        fields = [
            "title",
            "subject",
            "tracker",
            "priority",
            "start_time",
            "end_time",
            "notes",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Task title (optional if a habit is selected)",
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "tracker": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Notes (optional)",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False

        self.fields["tracker"].queryset = Tracker.objects.filter(
            user=user, is_active=True
        ).exclude(category=Tracker.Category.HEALTH)
        self.fields["tracker"].required = False
        self.fields["tracker"].label = "Habit / Tracker"

        self.fields["title"].required = False

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")

        title = cleaned.get("title")
        tracker = cleaned.get("tracker")

        if not title:
            if tracker:
                cleaned["title"] = tracker.name
            else:
                raise forms.ValidationError("Enter a title or select a habit.")

        return cleaned


class PomodoroSessionLogForm(forms.ModelForm):
    """Server-side validation for the JSON pomodoro-log endpoint. Never rendered/crispy."""

    class Meta:
        model = PomodoroSession

        fields = [
            "task",
            "subject",
            "topic",
            "session_type",
            "planned_duration_minutes",
            "actual_duration_seconds",
            "is_completed",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["task"].queryset = DailyTask.objects.filter(user=user)
        self.fields["task"].required = False

        self.fields["topic"].queryset = Topic.objects.filter(subject__user=user)
        self.fields["topic"].required = False

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("session_type") == PomodoroSession.SessionType.FOCUS:
            task = cleaned.get("task")
            subject = cleaned.get("subject")
            topic = cleaned.get("topic")

            if not task and not subject:
                raise forms.ValidationError("Select a task or subject before starting a Focus session.")

            if not task and subject and not topic:
                raise forms.ValidationError("Select a topic before starting a Focus session on a subject.")

        return cleaned

        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False
