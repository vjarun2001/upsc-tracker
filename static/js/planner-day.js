document.addEventListener("change", function (event) {
    const checkbox = event.target.closest(".task-toggle");
    if (!checkbox) {
        return;
    }

    fetch(checkbox.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.ok) {
                // Reload so the stat cards and Today/Scheduled/Pending buckets
                // (which are server-rendered and depend on is_completed) stay accurate.
                window.location.reload();
            }
        });
});

document.addEventListener("click", function (event) {
    const button = event.target.closest(".task-delete");
    if (!button) {
        return;
    }

    if (!confirm("Delete this task?")) {
        return;
    }

    fetch(button.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.ok) {
                window.location.reload();
            }
        });
});
