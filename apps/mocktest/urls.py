from django.urls import path

from . import views

app_name = "mocktest"

urlpatterns = [
    path("", views.test_list, name="list"),
    path("add/", views.add_test, name="add"),
    path("<int:pk>/edit/", views.edit_test, name="edit"),
    path("<int:pk>/delete/", views.delete_test, name="delete"),
    path("goal/", views.set_goal, name="set_goal"),
]
