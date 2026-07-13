from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("allauth.urls")),
    path(
        "accounts/",
        include(
            ("apps.accounts.urls", "accounts"),
            namespace="accounts",
        ),
    ),
    path(
        "study/",
        include(
            ("apps.study.urls", "study"),
            namespace="study",
        ),
    ),
    path(
        "planner/",
        include(
            ("apps.planner.urls", "planner"),
            namespace="planner",
        ),
    ),
    path(
        "notes/",
        include(
            ("apps.notes.urls", "notes"),
            namespace="notes",
        ),
    ),
    path(
        "goals/",
        include(
            ("apps.goals.urls", "goals"),
            namespace="goals",
        ),
    ),
    path(
        "revision/",
        include(
            ("apps.revision.urls", "revision"),
            namespace="revision",
        ),
    ),
    path(
        "mocktest/",
        include(
            ("apps.mocktest.urls", "mocktest"),
            namespace="mocktest",
        ),
    ),
    path(
        "analytics/",
        include(
            ("apps.analytics.urls", "analytics"),
            namespace="analytics",
        ),
    ),
    path(
        "activity/",
        include(
            ("apps.activity.urls", "activity"),
            namespace="activity",
        ),
    ),
    path(
        "calendar/",
        include(
            ("apps.calendarapp.urls", "calendarapp"),
            namespace="calendarapp",
        ),
    ),
    path(
        "tracker/",
        include(
            ("apps.tracker.urls", "tracker"),
            namespace="tracker",
        ),
    ),
]