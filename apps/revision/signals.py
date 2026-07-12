from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.study.models import Topic

from .models import RevisionSchedule

REVISION_INTERVALS_DAYS = [1, 3, 7, 15, 30]


@receiver(post_save, sender=Topic)
def schedule_revisions_on_completion(sender, instance, created, **kwargs):
    if created or not instance.is_completed:
        return

    if RevisionSchedule.objects.filter(topic=instance).exists():
        return

    today = timezone.localdate()

    RevisionSchedule.objects.bulk_create(
        [
            RevisionSchedule(
                user=instance.subject.user,
                topic=instance,
                stage_days=days,
                scheduled_date=today + timedelta(days=days),
            )
            for days in REVISION_INTERVALS_DAYS
        ]
    )
