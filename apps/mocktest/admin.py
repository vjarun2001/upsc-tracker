from django.contrib import admin

from .models import MockTest


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "test_date", "correct", "incorrect", "obtained_marks")
