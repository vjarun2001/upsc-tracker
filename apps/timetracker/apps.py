from django.apps import AppConfig


class TimetrackerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.timetracker"

    def ready(self):
        from . import signals  # noqa: F401
