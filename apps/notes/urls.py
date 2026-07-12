from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("add/", views.add_note, name="add"),
    path("<int:pk>/edit/", views.edit_note, name="edit"),
    path("<int:pk>/delete/", views.delete_note, name="delete"),
]
