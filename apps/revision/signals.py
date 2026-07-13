from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.study.models import Topic

from .models import RevisionSchedule

FIRST_STAGE_INTERVAL_DAYS = 1


@receiver(post_save, sender=Topic)
def schedule_first_revision_on_completion(sender, instance, created, **kwargs):
    if created or instance.status != Topic.Status.COMPLETED:
        return

    if RevisionSchedule.objects.filter(topic=instance).exists():
        return

    RevisionSchedule.objects.create(
        user=instance.subject.user,
        topic=instance,
        stage=1,
        scheduled_date=timezone.localdate() + timedelta(days=FIRST_STAGE_INTERVAL_DAYS),
    )
