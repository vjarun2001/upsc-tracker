from django import forms

from .models import Subject, Topic


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject

        fields = [
            "name",
            "color",
            "phase",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Subject name",
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "phase": forms.Select(attrs={"class": "form-select"}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic

        fields = [
            "subject",
            "parent",
            "title",
            "weightage",
        ]

        widgets = {
            "subject": forms.Select(attrs={"class": "form-select"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Topic title",
                }
            ),
            "weightage": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=user)
        self.fields["parent"].queryset = Topic.objects.filter(subject__user=user)
        self.fields["parent"].required = False
