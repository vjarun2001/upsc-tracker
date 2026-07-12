from django.urls import path

from . import views

app_name = "mocktest"

urlpatterns = [
    path("", views.test_list, name="list"),
    path("add/", views.add_test, name="add"),
    path("<int:pk>/delete/", views.delete_test, name="delete"),
]
