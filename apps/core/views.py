from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.common.choices import Phase


def home(request):
    return render(request, "home.html")


@login_required
def set_phase(request, phase):
    if phase in Phase.values:
        request.session["active_phase"] = phase

    next_url = request.GET.get("next")

    if not next_url or not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        next_url = reverse("core:home")

    return redirect(next_url)


def service_worker(request):
    sw_path = Path(settings.BASE_DIR) / "static" / "sw.js"
    return HttpResponse(sw_path.read_text(), content_type="application/javascript")
