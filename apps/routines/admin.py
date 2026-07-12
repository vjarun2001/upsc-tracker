from django.contrib import admin

from .models import Routine, RoutineLog


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_minutes", "is_active")


@admin.register(RoutineLog)
class RoutineLogAdmin(admin.ModelAdmin):
    list_display = ("routine", "date", "minutes_spent", "logged_at")
