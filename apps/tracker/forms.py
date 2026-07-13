from django import forms

from .models import Tracker


class TrackerForm(forms.ModelForm):
    class Meta:
        model = Tracker

        fields = ["name", "kind", "target_value", "icon"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Morning Walk"}
            ),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "target_value": forms.NumberInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "bi-check2-circle"}
            ),
        }
