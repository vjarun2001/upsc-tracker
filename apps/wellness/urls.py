from django.urls import path

from . import views

app_name = "wellness"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("sleep/log/", views.log_sleep, name="log_sleep"),
    path("water/log/", views.log_water, name="log_water"),
    path("habits/add/", views.add_habit, name="add_habit"),
    path("habits/<int:pk>/toggle/", views.toggle_habit, name="toggle_habit"),
    path("meals/<str:meal_type>/toggle/", views.toggle_meal, name="toggle_meal"),
]
