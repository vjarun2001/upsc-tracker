def flatten_topics(topics):
    """Return [(topic, depth), ...] in depth-first order given a flat topic list."""
    by_parent = {}
    for topic in topics:
        by_parent.setdefault(topic.parent_id, []).append(topic)

    result = []

    def walk(parent_id, depth):
        for topic in sorted(by_parent.get(parent_id, []), key=lambda t: t.title):
            result.append((topic, depth))
            walk(topic.id, depth + 1)

    walk(None, 0)

    return result
