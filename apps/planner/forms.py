from django import forms

from apps.study.models import Subject

from .models import DailyTask, PomodoroSession


class DailyTaskForm(forms.ModelForm):
    class Meta:
        model = DailyTask

        fields = [
            "title",
            "subject",
            "start_time",
            "end_time",
            "notes",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Task title",
                }
            ),
            "subject": forms.Select(
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

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned


class PomodoroSessionLogForm(forms.ModelForm):
    """Server-side validation for the JSON pomodoro-log endpoint. Never rendered/crispy."""

    class Meta:
        model = PomodoroSession

        fields = [
            "task",
            "subject",
            "session_type",
            "planned_duration_minutes",
            "actual_duration_seconds",
            "is_completed",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["task"].queryset = DailyTask.objects.filter(user=user)
        self.fields["task"].required = False

        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False
