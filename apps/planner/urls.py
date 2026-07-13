from django.urls import path

from . import views

app_name = "planner"

urlpatterns = [
    path(
        "",
        views.day_view,
        name="day_today",
    ),
    path(
        "tasks/",
        views.board,
        name="board",
    ),
    path(
        "<int:year>/<int:month>/<int:day>/",
        views.day_view,
        name="day",
    ),
    path(
        "task/add/",
        views.add_task,
        name="add_task",
    ),
    path(
        "task/<int:pk>/toggle/",
        views.toggle_task,
        name="toggle_task",
    ),
    path(
        "task/<int:pk>/edit/",
        views.edit_task,
        name="edit_task",
    ),
    path(
        "task/<int:pk>/delete/",
        views.delete_task,
        name="delete_task",
    ),
    path(
        "pomodoro/",
        views.pomodoro,
        name="pomodoro",
    ),
    path(
        "pomodoro/log/",
        views.log_pomodoro_session,
        name="log_pomodoro_session",
    ),
]
