from django.urls import path

from . import views

app_name = "goals"

urlpatterns = [
    path("", views.goal_list, name="list"),
    path("add/", views.add_goal, name="add"),
    path("<int:pk>/edit/", views.edit_goal, name="edit"),
    path("<int:pk>/toggle/", views.toggle_goal, name="toggle"),
    path("<int:pk>/delete/", views.delete_goal, name="delete"),
    path("<int:goal_pk>/milestones/add/", views.add_milestone, name="add_milestone"),
    path("milestones/<int:pk>/toggle/", views.toggle_milestone, name="toggle_milestone"),
]
