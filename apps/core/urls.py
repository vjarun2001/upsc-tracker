from django.urls import path

from .views import home, service_worker, set_phase

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("sw.js", service_worker, name="service_worker"),
    path("phase/<str:phase>/", set_phase, name="set_phase"),
]
