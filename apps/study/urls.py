from django.urls import path

from . import views

app_name = "study"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "add-subject/",
        views.add_subject,
        name="add_subject",
    ),
    path(
        "add-topic/",
        views.add_topic,
        name="add_topic",
    ),
    path(
        "topic/<int:pk>/toggle/",
        views.toggle_topic,
        name="toggle_topic",
    ),
]