from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
]
