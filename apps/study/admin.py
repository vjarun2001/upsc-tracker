from django.contrib import admin

from .models import Subject, Topic, StudySession


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "is_completed")


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "user",
        "start_time",
        "end_time",
    )