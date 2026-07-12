from django import forms

from apps.study.models import Subject

from .models import MockTest


class MockTestForm(forms.ModelForm):
    class Meta:
        model = MockTest

        fields = [
            "name",
            "subject",
            "test_date",
            "total_questions",
            "correct",
            "incorrect",
            "marks_per_correct",
            "negative_marks_per_incorrect",
            "notes",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mock test name"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "test_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "total_questions": forms.NumberInput(attrs={"class": "form-control"}),
            "correct": forms.NumberInput(attrs={"class": "form-control"}),
            "incorrect": forms.NumberInput(attrs={"class": "form-control"}),
            "marks_per_correct": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "negative_marks_per_incorrect": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False

    def clean(self):
        cleaned = super().clean()

        total = cleaned.get("total_questions")
        correct = cleaned.get("correct")
        incorrect = cleaned.get("incorrect")

        if total is not None and correct is not None and incorrect is not None:
            if correct + incorrect > total:
                raise forms.ValidationError(
                    "Correct + incorrect cannot exceed total questions."
                )

        return cleaned
