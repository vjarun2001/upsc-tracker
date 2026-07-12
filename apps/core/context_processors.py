import random

from .models import Quote


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
