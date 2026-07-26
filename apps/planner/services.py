from apps.activity.services import log_activity


def mark_task_completed(task):
    """Mark a task done, syncing its linked tracker log and the activity feed."""
    if not task.is_completed:
        task.is_completed = True
        task.save(update_fields=["is_completed"])

    log_activity(
        task.user,
        "task_completed",
        f"Completed task: {task.title}",
        url="/planner/",
        icon="bi-check-square",
    )

    if task.tracker_id:
        log, _ = task.tracker.logs.get_or_create(date=task.date)
        if not log.value:
            log.value = task.tracker.target_value if task.tracker.kind != task.tracker.Kind.BOOLEAN else 1
            log.save(update_fields=["value"])
