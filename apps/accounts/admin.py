from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LoginSession, Profile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("email",)

    list_display = (
        "email",
        "full_name",
        "is_staff",
        "is_email_verified",
    )

    search_fields = ("email", "full_name")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal",
            {
                "fields": (
                    "full_name",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


admin.site.register(Profile)


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "login_at", "last_seen_at", "logout_at", "duration_seconds")
    list_filter = ("date",)