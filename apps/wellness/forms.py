from django import forms

from .models import Habit, SleepLog, WaterLog


class SleepLogForm(forms.ModelForm):
    class Meta:
        model = SleepLog
        fields = ["hours", "quality", "notes"]
        widgets = {
            "hours": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.5", "min": "0", "max": "24"}
            ),
            "quality": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notes"}),
        }


class WaterLogForm(forms.ModelForm):
    class Meta:
        model = WaterLog
        fields = ["glasses", "target"]
        widgets = {
            "glasses": forms.NumberInput(attrs={"class": "form-control"}),
            "target": forms.NumberInput(attrs={"class": "form-control"}),
        }


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Read newspaper"}
            ),
        }
