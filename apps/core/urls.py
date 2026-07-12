from django.urls import path

from .views import home, service_worker

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("sw.js", service_worker, name="service_worker"),
]
