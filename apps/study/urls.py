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
        "subject/<int:pk>/edit/",
        views.edit_subject,
        name="edit_subject",
    ),
    path(
        "add-topic/",
        views.add_topic,
        name="add_topic",
    ),
    path(
        "topic/<int:pk>/update/",
        views.update_topic,
        name="update_topic",
    ),
]