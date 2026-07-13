from .models import MockTest


def score_and_accuracy_trend(user, phase=None):
    tests = MockTest.objects.filter(user=user).order_by("test_date")

    if phase:
        tests = tests.filter(phase=phase)

    labels = [t.test_date.strftime("%d %b") for t in tests]
    scores = [float(t.obtained_marks) for t in tests]
    accuracy = [t.accuracy_percent for t in tests]

    return labels, scores, accuracy


def summary_stats(user, phase=None):
    tests = MockTest.objects.filter(user=user)

    if phase:
        tests = tests.filter(phase=phase)

    tests = list(tests)

    if not tests:
        return {
            "avg_score": 0,
            "avg_accuracy": 0,
            "tests_taken": 0,
            "best_score": 0,
            "last_mistakes": None,
        }

    scores = [float(t.obtained_marks) for t in tests]
    accuracies = [t.accuracy_percent for t in tests]

    latest = max(tests, key=lambda t: t.test_date)

    return {
        "avg_score": round(sum(scores) / len(scores)),
        "avg_accuracy": round(sum(accuracies) / len(accuracies)),
        "tests_taken": len(tests),
        "best_score": round(max(scores)),
        "last_mistakes": latest.incorrect,
    }
