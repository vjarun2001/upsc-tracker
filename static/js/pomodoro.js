(function () {
    const typeButtons = document.querySelectorAll(".type-btn");
    const minutesInput = document.getElementById("minutes-input");
    const display = document.getElementById("timer-display");
    const startBtn = document.getElementById("btn-start");
    const pauseBtn = document.getElementById("btn-pause");
    const resumeBtn = document.getElementById("btn-resume");
    const stopBtn = document.getElementById("btn-stop");
    const taskSelect = document.getElementById("task-select");
    const subjectSelect = document.getElementById("subject-select");
    const topicSelect = document.getElementById("topic-select");
    const historyList = document.getElementById("session-history");
    const focusWarning = document.getElementById("focus-link-warning");

    const topicsBySubjectEl = document.getElementById("topics-by-subject");
    const topicsBySubject = topicsBySubjectEl ? JSON.parse(topicsBySubjectEl.textContent) : {};

    let sessionType = "focus";

    function populateTopics(subjectId, selectedTopicId) {
        topicSelect.innerHTML = "";

        const topics = topicsBySubject[subjectId] || [];

        if (!subjectId) {
            topicSelect.appendChild(new Option("-- Select a subject first --", ""));
            topicSelect.disabled = true;
            return;
        }

        if (!topics.length) {
            topicSelect.appendChild(new Option("-- No topics under this subject --", ""));
            topicSelect.disabled = true;
            return;
        }

        topicSelect.appendChild(new Option("-- None --", ""));
        topics.forEach((topic) => {
            topicSelect.appendChild(new Option(topic.title, topic.id));
        });
        topicSelect.disabled = false;

        if (selectedTopicId) topicSelect.value = selectedTopicId;
    }

    subjectSelect.addEventListener("change", () => {
        populateTopics(subjectSelect.value, null);
    });

    function render(remaining) {
        const minutes = Math.floor(remaining / 60).toString().padStart(2, "0");
        const seconds = (remaining % 60).toString().padStart(2, "0");
        display.textContent = `${minutes}:${seconds}`;
        display.classList.toggle("text-danger", remaining > 0 && remaining <= 10);
    }

    function setButtons({ start, pause, resume, stop }) {
        startBtn.classList.toggle("d-none", !start);
        pauseBtn.classList.toggle("d-none", !pause);
        resumeBtn.classList.toggle("d-none", !resume);
        stopBtn.classList.toggle("d-none", !stop);
    }

    function setControlsDisabled(disabled) {
        typeButtons.forEach((btn) => (btn.disabled = disabled));
        minutesInput.disabled = disabled;
        taskSelect.disabled = disabled;
        subjectSelect.disabled = disabled;

        if (disabled) {
            topicSelect.disabled = true;
        } else {
            populateTopics(subjectSelect.value, topicSelect.value);
        }
    }

    function resetTimer() {
        setControlsDisabled(false);
        const totalSeconds = parseInt(minutesInput.value, 10) * 60;
        render(totalSeconds);
        setButtons({ start: true, pause: false, resume: false, stop: false });
        focusWarning.classList.add("d-none");
    }

    typeButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.disabled) return;
            typeButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            sessionType = btn.dataset.type;
            minutesInput.value = btn.dataset.minutes;
            resetTimer();
        });
    });

    minutesInput.addEventListener("change", () => {
        if (!minutesInput.disabled) resetTimer();
    });

    startBtn.addEventListener("click", () => {
        if (sessionType === "focus") {
            if (!taskSelect.value && !subjectSelect.value) {
                focusWarning.textContent = "Select a task, or a subject + topic, before starting a Focus session.";
                focusWarning.classList.remove("d-none");
                return;
            }
            if (!taskSelect.value && subjectSelect.value && !topicSelect.value) {
                focusWarning.textContent = "Select a topic before starting a Focus session on a subject.";
                focusWarning.classList.remove("d-none");
                return;
            }
        }
        focusWarning.classList.add("d-none");

        window.PomodoroCore.unlockAudio();
        window.PomodoroCore.start({
            sessionType: sessionType,
            totalSeconds: parseInt(minutesInput.value, 10) * 60,
            taskId: taskSelect.value || null,
            subjectId: subjectSelect.value || null,
            topicId: topicSelect.value || null,
        });

        setControlsDisabled(true);
        setButtons({ start: false, pause: true, resume: false, stop: true });
    });

    pauseBtn.addEventListener("click", () => {
        window.PomodoroCore.pause();
        setButtons({ start: false, pause: false, resume: true, stop: true });
    });

    resumeBtn.addEventListener("click", () => {
        window.PomodoroCore.resume();
        setButtons({ start: false, pause: true, resume: false, stop: true });
    });

    stopBtn.addEventListener("click", () => {
        window.PomodoroCore.stop();
        resetTimer();
    });

    function appendHistory(session) {
        const item = document.createElement("li");
        item.className = "list-group-item d-flex justify-content-between";
        const minutes = Math.round(session.actual_duration_seconds / 60);
        item.innerHTML = `<span>${session.session_type}</span><span>${minutes} min ${
            session.is_completed ? "✅" : "⏹"
        }</span>`;
        historyList.prepend(item);
    }

    window.PomodoroCore.onTick(function (state, remaining) {
        if (!state) {
            resetTimer();
            return;
        }
        render(remaining);
        setButtons({
            start: false,
            pause: !state.paused,
            resume: state.paused,
            stop: true,
        });
    });

    window.PomodoroCore.onComplete(function (data) {
        if (data && data.ok) {
            appendHistory(data.session);
        }
    });

    // Restore an in-progress session (e.g. the user navigated back to this page).
    const existing = window.PomodoroCore.getState();
    if (existing) {
        sessionType = existing.sessionType;
        minutesInput.value = Math.round(existing.totalSeconds / 60);
        typeButtons.forEach((b) => b.classList.toggle("active", b.dataset.type === sessionType));
        taskSelect.value = existing.taskId || "";
        subjectSelect.value = existing.subjectId || "";
        populateTopics(existing.subjectId, existing.topicId);
        setControlsDisabled(true);
        render(window.PomodoroCore.remainingSeconds());
        setButtons({
            start: false,
            pause: !existing.paused,
            resume: existing.paused,
            stop: true,
        });
    } else {
        const configEl = document.getElementById("planner-config");
        if (configEl) {
            const config = JSON.parse(configEl.textContent);
            if (config.preselected_task) taskSelect.value = config.preselected_task;
            if (config.preselected_subject) subjectSelect.value = config.preselected_subject;
        }
        populateTopics(subjectSelect.value, null);
        resetTimer();
    }
})();
