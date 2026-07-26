from django import forms

from .models import Activity


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity

        fields = ["name", "color", "icon"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. GS2, Optional, Newspaper"}
            ),
            "color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "icon": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "bi-bookmark"}
            ),
        }
