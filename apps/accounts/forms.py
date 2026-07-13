from django import forms

from apps.core.models import ExamProfile

from .models import Profile, User


class UserForm(forms.ModelForm):
    class Meta:
        model = User

        fields = [
            "full_name",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full name",
                }
            ),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = [
            "avatar",
            "phone",
            "timezone",
            "bio",
        ]

        widgets = {
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "timezone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Asia/Kolkata",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "A little about your UPSC prep journey",
                }
            ),
        }


class ExamProfileForm(forms.ModelForm):
    class Meta:
        model = ExamProfile

        fields = [
            "prelims_date",
            "mains_date",
            "interview_date",
        ]

        widgets = {
            "prelims_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "mains_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "interview_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
