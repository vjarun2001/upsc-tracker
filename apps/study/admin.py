from django.contrib import admin

from .models import Subject, Topic, StudySession


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "phase")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "status", "confidence", "weightage")


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "user",
        "start_time",
        "end_time",
    )
