from django.contrib import admin

from .models import Habit, HabitLog, MealLog, SleepLog, WaterLog


@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "hours", "quality")


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "glasses", "target")


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_active")


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("habit", "date", "is_done")


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "meal_type", "eaten", "eaten_at")
