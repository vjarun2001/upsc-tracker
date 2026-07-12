(function () {
    const badge = document.getElementById("session-badge");
    if (!badge) return;

    let seconds = parseInt(badge.dataset.seconds, 10) || 0;

    function render() {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        badge.textContent = h > 0 ? `${h}h ${m}m` : `${m}m`;
    }

    render();

    setInterval(function () {
        seconds += 1;
        render();
    }, 1000);

    function ping() {
        fetch(badge.dataset.heartbeatUrl, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
        })
            .then((response) => response.json())
            .then((data) => {
                if (typeof data.today_seconds === "number") {
                    seconds = data.today_seconds;
                    render();
                }
            })
            .catch(() => {});
    }

    setInterval(ping, 60000);
})();
