from django.urls import path

from . import views

app_name = "revision"

urlpatterns = [
    path("", views.today_view, name="today"),
    path("<int:pk>/done/", views.mark_done, name="mark_done"),
]
