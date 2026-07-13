from django.contrib import admin

from .models import MockTest, TestGoal


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "phase", "test_date", "correct", "incorrect", "obtained_marks")


@admin.register(TestGoal)
class TestGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "target_score", "target_accuracy", "next_test_date")
