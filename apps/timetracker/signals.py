from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User

from .models import Activity

DEFAULT_ACTIVITIES = [
    {"name": "Study", "kind": Activity.Kind.STUDY, "icon": "bi-journal-text", "color": "#0d6efd", "order": 0},
    {"name": "Tuition", "kind": Activity.Kind.TUITION, "icon": "bi-easel", "color": "#6f42c1", "order": 1},
    {"name": "Break", "kind": Activity.Kind.BREAK, "icon": "bi-cup-hot", "color": "#fd7e14", "order": 2},
    {"name": "Others", "kind": Activity.Kind.OTHERS, "icon": "bi-three-dots", "color": "#6c757d", "order": 3},
]


@receiver(post_save, sender=User)
def create_default_activities(sender, instance, created, **kwargs):
    if not created:
        return

    Activity.objects.bulk_create(
        [Activity(user=instance, **defaults) for defaults in DEFAULT_ACTIVITIES]
    )
