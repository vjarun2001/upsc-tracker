from django import forms

from apps.study.models import Subject, Topic

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note

        fields = [
            "title",
            "subject",
            "topic",
            "content",
            "is_pinned",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Note title",
                }
            ),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "topic": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Write your note...",
                }
            ),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["subject"].required = False

        self.fields["topic"].queryset = Topic.objects.filter(subject__user=user)
        self.fields["topic"].required = False
