from django.conf import settings
from django.db import migrations

DEFAULT_ACTIVITIES = [
    {"name": "Study", "kind": "study", "icon": "bi-journal-text", "color": "#0d6efd", "order": 0},
    {"name": "Tuition", "kind": "tuition", "icon": "bi-easel", "color": "#6f42c1", "order": 1},
    {"name": "Break", "kind": "break", "icon": "bi-cup-hot", "color": "#fd7e14", "order": 2},
    {"name": "Others", "kind": "others", "icon": "bi-three-dots", "color": "#6c757d", "order": 3},
]


def seed_default_activities(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Activity = apps.get_model("timetracker", "Activity")

    for user in User.objects.all():
        for defaults in DEFAULT_ACTIVITIES:
            name = defaults["name"]
            kind = defaults["kind"]
            activity, created = Activity.objects.get_or_create(
                user=user, name=name, defaults={k: v for k, v in defaults.items() if k != "name"}
            )
            # A same-named Activity the user already created themselves (e.g. their own
            # "Study" category) matches on name but keeps its old kind="custom" — upgrade
            # it so the special Study/Break/Others behavior applies to their existing data too.
            if not created and activity.kind != kind:
                activity.kind = kind
                activity.save(update_fields=["kind"])


def remove_default_activities(apps, schema_editor):
    Activity = apps.get_model("timetracker", "Activity")
    Activity.objects.filter(name__in=[d["name"] for d in DEFAULT_ACTIVITIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("timetracker", "0002_activity_kind_breaksession_planned_minutes_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_default_activities, remove_default_activities),
    ]
