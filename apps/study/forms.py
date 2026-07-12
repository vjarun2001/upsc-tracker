from django import forms

from .models import Subject, Topic


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject

        fields = [
            "name",
            "color",
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
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic

        fields = [
            "subject",
            "title",
        ]

        widgets = {
            "subject": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Topic title",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(user=user)
