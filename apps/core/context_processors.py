import random

from django.utils import timezone

from apps.common.choices import Phase

from .models import ExamProfile, Quote


def phase_tabs(request):
    if not request.user.is_authenticated:
        return {"phase_tabs": []}

    profile, _ = ExamProfile.objects.get_or_create(user=request.user)

    today = timezone.localdate()
    current = request.session.get("active_phase", Phase.PRELIMS.value)

    date_map = {
        Phase.PRELIMS.value: profile.prelims_date,
        Phase.MAINS.value: profile.mains_date,
        Phase.INTERVIEW.value: profile.interview_date,
    }

    tabs = []
    for key, label in Phase.choices:
        target_date = date_map.get(key)
        days_remaining = (target_date - today).days if target_date else None

        tabs.append(
            {
                "key": key,
                "label": label,
                "days_remaining": days_remaining,
                "is_active": key == current,
            }
        )

    return {"phase_tabs": tabs}


def login_quote(request):
    if request.method != "GET" or not request.user.is_authenticated:
        return {"login_quote": None}

    from apps.accounts.models import LoginSession

    session = (
        LoginSession.objects.filter(user=request.user, quote_shown=False)
        .order_by("-login_at")
        .first()
    )

    if not session:
        return {"login_quote": None}

    quote_ids = list(Quote.objects.filter(is_active=True).values_list("id", flat=True))

    session.quote_shown = True
    session.save(update_fields=["quote_shown"])

    if not quote_ids:
        return {"login_quote": None}

    quote = Quote.objects.get(pk=random.choice(quote_ids))

    return {"login_quote": quote}
