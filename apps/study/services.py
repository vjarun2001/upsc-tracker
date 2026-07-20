def flatten_topics(topics):
    """Return [(topic, depth), ...] in depth-first order given a flat topic list."""
    by_parent = {}
    for topic in topics:
        by_parent.setdefault(topic.parent_id, []).append(topic)

    result = []

    def walk(parent_id, depth):
        for topic in sorted(by_parent.get(parent_id, []), key=lambda t: (t.order, t.id)):
            result.append((topic, depth))
            walk(topic.id, depth + 1)

    walk(None, 0)

    return result


def time_of_day_bucket(t):
    """Classify a datetime.time into morning/afternoon/evening/night."""
    if 5 <= t.hour < 12:
        return "morning"
    if 12 <= t.hour < 17:
        return "afternoon"
    if 17 <= t.hour < 21:
        return "evening"
    return "night"


def descendant_ids(topic, all_topics):
    """Return the set of pks of every descendant of `topic` within `all_topics`."""
    children_by_parent = {}
    for t in all_topics:
        children_by_parent.setdefault(t.parent_id, []).append(t)

    ids = set()

    def walk(parent_id):
        for child in children_by_parent.get(parent_id, []):
            ids.add(child.id)
            walk(child.id)

    walk(topic.id)

    return ids
