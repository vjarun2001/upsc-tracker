document.addEventListener("change", function (event) {
    const checkbox = event.target.closest(".task-toggle");
    if (!checkbox) {
        return;
    }

    const row = checkbox.closest("[data-task-row]");

    fetch(checkbox.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.ok) {
                row.classList.toggle("text-decoration-line-through", data.is_completed);
                row.classList.toggle("text-muted", data.is_completed);
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

    const row = button.closest("[data-task-row]");

    fetch(button.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.ok) {
                row.remove();
            }
        });
});
