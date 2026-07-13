from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add/", views.add_tracker, name="add"),
    path("<int:pk>/edit/", views.edit_tracker, name="edit"),
    path("<int:pk>/delete/", views.delete_tracker, name="delete"),
    path("<int:pk>/log/", views.log_tracker, name="log"),
]
