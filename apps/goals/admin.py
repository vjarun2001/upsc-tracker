from django.contrib import admin

from .models import Goal, Milestone


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 1


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "target_date", "is_completed")
    list_filter = ("is_completed",)
    inlines = [MilestoneInline]
