from django.contrib import admin

from .models import ExamProfile, Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("text", "author", "is_active")
    list_filter = ("is_active",)


@admin.register(ExamProfile)
class ExamProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "prelims_date", "mains_date", "interview_date")
