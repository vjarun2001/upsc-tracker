from django.urls import path

from . import views

app_name = "calendarapp"

urlpatterns = [
    path("", views.day_view, name="day_today"),
    path("day/<int:year>/<int:month>/<int:day>/", views.day_view, name="day"),
    path("week/", views.week_view, name="week_today"),
    path("week/<int:year>/<int:month>/<int:day>/", views.week_view, name="week"),
    path("month/", views.month_view, name="month_today"),
    path("month/<int:year>/<int:month>/", views.month_view, name="month"),
]
