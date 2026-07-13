from datetime import timedelta

from django.utils import timezone

from .models import RevisionSchedule

MAX_STAGE = 5

# Base gap in days from stage N to stage N+1, before confidence scaling.
BASE_GAP_DAYS = {1: 2, 2: 4, 3: 7, 4: 15}

CONFIDENCE_MULTIPLIER = {
    RevisionSchedule.Confidence.LOW: 0.5,
    RevisionSchedule.Confidence.MEDIUM: 1.0,
    RevisionSchedule.Confidence.HIGH: 1.75,
}


def advance_revision(schedule, confidence):
    """Mark a revision stage done and, if not final, schedule the next stage.

    Interval to the next stage scales with confidence: low confidence means
    the topic needs reinforcement sooner, high confidence means it can wait
    longer — real spaced repetition rather than a fixed schedule.
    """
    schedule.is_done = True
    schedule.confidence = confidence
    schedule.done_at = timezone.now()
    schedule.save(update_fields=["is_done", "confidence", "done_at"])

    if schedule.stage >= MAX_STAGE:
        return None

    base_gap = BASE_GAP_DAYS.get(schedule.stage, 15)
    multiplier = CONFIDENCE_MULTIPLIER.get(confidence, 1.0)
    gap_days = max(1, round(base_gap * multiplier))

    next_stage = RevisionSchedule.objects.create(
        user=schedule.user,
        topic=schedule.topic,
        stage=schedule.stage + 1,
        scheduled_date=timezone.localdate() + timedelta(days=gap_days),
    )

    return next_stage
