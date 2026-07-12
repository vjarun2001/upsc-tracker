from django.urls import path

from . import views

app_name = "routines"

urlpatterns = [
    path("", views.list_routines, name="list"),
    path("add/", views.add_routine, name="add"),
    path("<int:pk>/delete/", views.delete_routine, name="delete"),
    path("<int:pk>/log/", views.log_routine, name="log"),
]
