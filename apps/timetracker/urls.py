from django.urls import path

from . import views

app_name = "timetracker"

urlpatterns = [
    path("", views.timer_page, name="timer_page"),
    path("timeline/", views.timeline_page, name="timeline_page"),
    path("history/", views.history_view, name="history"),
    path("activities/", views.activity_list, name="activity_list"),
    path("activities/<int:pk>/", views.activity_detail, name="activity_detail"),
    path("activities/add/", views.add_activity, name="add_activity"),
    path("activities/<int:pk>/edit/", views.edit_activity, name="edit_activity"),
    path("activities/<int:pk>/archive/", views.archive_activity, name="archive_activity"),
    path("activities/<int:pk>/restore/", views.restore_activity, name="restore_activity"),
    path("activities/<int:pk>/delete/", views.delete_activity, name="delete_activity"),
    path("session/start/", views.start_session_view, name="start_session"),
    path("session/pause/", views.pause_session_view, name="pause_session"),
    path("session/resume/", views.resume_session_view, name="resume_session"),
    path("session/stop/", views.stop_session_view, name="stop_session"),
    path("break/start/", views.start_break_view, name="start_break"),
    path("break/end/", views.end_break_view, name="end_break"),
    path("summary/", views.summary_view, name="summary"),
    path("timeline/data/", views.timeline_data_view, name="timeline_data"),
]
