from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def service_worker(request):
    sw_path = Path(settings.BASE_DIR) / "static" / "sw.js"
    return HttpResponse(sw_path.read_text(), content_type="application/javascript")
