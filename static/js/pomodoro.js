(function () {
    const config = JSON.parse(document.getElementById("planner-config").textContent);

    const typeButtons = document.querySelectorAll(".type-btn");
    const minutesInput = document.getElementById("minutes-input");
    const display = document.getElementById("timer-display");
    const startBtn = document.getElementById("btn-start");
    const pauseBtn = document.getElementById("btn-pause");
    const resumeBtn = document.getElementById("btn-resume");
    const stopBtn = document.getElementById("btn-stop");
    const taskSelect = document.getElementById("task-select");
    const subjectSelect = document.getElementById("subject-select");
    const historyList = document.getElementById("session-history");

    let sessionType = "focus";
    let totalSeconds = parseInt(minutesInput.value, 10) * 60;
    let secondsLeft = totalSeconds;
    let intervalId = null;

    if (config.preselected_task) {
        taskSelect.value = config.preselected_task;
    }
    if (config.preselected_subject) {
        subjectSelect.value = config.preselected_subject;
    }

    function render() {
        const minutes = Math.floor(secondsLeft / 60)
            .toString()
            .padStart(2, "0");
        const seconds = (secondsLeft % 60).toString().padStart(2, "0");
        display.textContent = `${minutes}:${seconds}`;
    }

    function setButtons({ start, pause, resume, stop }) {
        startBtn.classList.toggle("d-none", !start);
        pauseBtn.classList.toggle("d-none", !pause);
        resumeBtn.classList.toggle("d-none", !resume);
        stopBtn.classList.toggle("d-none", !stop);
    }

    function resetTimer() {
        clearInterval(intervalId);
        intervalId = null;
        totalSeconds = parseInt(minutesInput.value, 10) * 60;
        secondsLeft = totalSeconds;
        render();
        setButtons({ start: true, pause: false, resume: false, stop: false });
    }

    typeButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            typeButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            sessionType = btn.dataset.type;
            minutesInput.value = btn.dataset.minutes;
            resetTimer();
        });
    });

    minutesInput.addEventListener("change", resetTimer);

    function tick() {
        secondsLeft -= 1;
        render();

        if (secondsLeft <= 0) {
            clearInterval(intervalId);
            intervalId = null;
            logSession(totalSeconds, true);
            setButtons({ start: true, pause: false, resume: false, stop: false });
        }
    }

    startBtn.addEventListener("click", () => {
        setButtons({ start: false, pause: true, resume: false, stop: true });
        intervalId = setInterval(tick, 1000);
    });

    pauseBtn.addEventListener("click", () => {
        clearInterval(intervalId);
        intervalId = null;
        setButtons({ start: false, pause: false, resume: true, stop: true });
    });

    resumeBtn.addEventListener("click", () => {
        setButtons({ start: false, pause: true, resume: false, stop: true });
        intervalId = setInterval(tick, 1000);
    });

    stopBtn.addEventListener("click", () => {
        clearInterval(intervalId);
        intervalId = null;
        const elapsed = totalSeconds - secondsLeft;
        logSession(elapsed, false);
        resetTimer();
    });

    function logSession(actualSeconds, isCompleted) {
        fetch(config.log_url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                session_type: sessionType,
                planned_duration_minutes: parseInt(minutesInput.value, 10),
                actual_duration_seconds: actualSeconds,
                is_completed: isCompleted,
                task: taskSelect.value || null,
                subject: subjectSelect.value || null,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.ok) {
                    appendHistory(data.session);
                }
            });
    }

    function appendHistory(session) {
        const item = document.createElement("li");
        item.className = "list-group-item d-flex justify-content-between";
        const minutes = Math.round(session.actual_duration_seconds / 60);
        item.innerHTML = `<span>${session.session_type}</span><span>${minutes} min ${
            session.is_completed ? "✅" : "⏹"
        }</span>`;
        historyList.prepend(item);
    }

    render();
})();
