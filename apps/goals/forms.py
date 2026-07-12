from django import forms

from apps.study.models import Subject

from .models import Goal, Milestone


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal

        fields = ["title", "subject", "description", "target_date"]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Goal title"}
            ),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "target_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Milestone"}
            ),
        }
