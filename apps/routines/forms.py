from django import forms

from .models import Routine, RoutineLog


class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        fields = ["name", "target_minutes"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Answer Writing Practice"}
            ),
            "target_minutes": forms.NumberInput(attrs={"class": "form-control"}),
        }


class RoutineLogForm(forms.ModelForm):
    class Meta:
        model = RoutineLog
        fields = ["minutes_spent", "logged_time", "notes"]
        widgets = {
            "minutes_spent": forms.NumberInput(attrs={"class": "form-control"}),
            "logged_time": forms.TimeInput(
                format="%H:%M", attrs={"type": "time", "class": "form-control"}
            ),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notes"}),
        }
