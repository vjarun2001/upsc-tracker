from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User

from .models import Tracker

DEFAULT_TRACKERS = [
    {"name": "Sleep", "kind": Tracker.Kind.DURATION, "target_value": 480, "icon": "bi-moon-stars", "category": Tracker.Category.HEALTH},
    {"name": "Water (Litres)", "kind": Tracker.Kind.COUNT, "target_value": 5, "icon": "bi-droplet", "category": Tracker.Category.HEALTH},
    {"name": "Breakfast", "kind": Tracker.Kind.BOOLEAN, "target_value": 1, "icon": "bi-cup-hot", "category": Tracker.Category.HEALTH},
    {"name": "Lunch", "kind": Tracker.Kind.BOOLEAN, "target_value": 1, "icon": "bi-cup-hot", "category": Tracker.Category.HEALTH},
    {"name": "Dinner", "kind": Tracker.Kind.BOOLEAN, "target_value": 1, "icon": "bi-cup-hot", "category": Tracker.Category.HEALTH},
]


@receiver(post_save, sender=User)
def create_default_trackers(sender, instance, created, **kwargs):
    if not created:
        return

    Tracker.objects.bulk_create(
        [Tracker(user=instance, **defaults) for defaults in DEFAULT_TRACKERS]
    )
