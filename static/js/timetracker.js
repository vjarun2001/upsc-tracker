(function () {
    const topicsBySubject = JSON.parse(document.getElementById("topics-by-subject").textContent);
    let summary = JSON.parse(document.getElementById("initial-summary").textContent);

    const statusBadge = document.getElementById("status-badge");
    const elapsedDisplay = document.getElementById("elapsed-display");
    const elapsedLabel = document.getElementById("elapsed-label");
    const goalProgressBar = document.getElementById("goal-progress-bar");
    const stateGroups = document.querySelectorAll("[data-state-group]");
    const breakStartWrap = document.getElementById("break-start-wrap");
    const breakCountdown = document.getElementById("break-countdown");
    const startSomethingElseWrap = document.getElementById("start-something-else-wrap");
    const toggleStartSomethingElse = document.getElementById("toggle-start-something-else");

    let hasAlertedThisBreak = false;

    const STATUS_META = {
        idle: { label: "Idle", badgeClass: "bg-secondary" },
        running: { label: "Running", badgeClass: "bg-primary" },
        paused: { label: "Paused", badgeClass: "bg-secondary" },
        on_break: { label: "On Break", badgeClass: "bg-warning text-dark" },
    };

    function formatHMS(totalSeconds) {
        totalSeconds = Math.max(0, Math.floor(totalSeconds));
        const h = Math.floor(totalSeconds / 3600).toString().padStart(2, "0");
        const m = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, "0");
        const s = (totalSeconds % 60).toString().padStart(2, "0");
        return `${h}:${m}:${s}`;
    }

    function formatMinutesHM(totalMinutes) {
        totalMinutes = Math.max(0, Math.round(totalMinutes || 0));
        const h = Math.floor(totalMinutes / 60);
        const m = totalMinutes % 60;
        return `${h}h ${m}m`;
    }

    // Short synthesized beep (no audio asset file) — same Web Audio oscillator technique
    // proven in this project's earlier Pomodoro timer, reused here for the break-ending alert.
    let audioCtx = null;
    function playBeep() {
        try {
            audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            oscillator.type = "sine";
            oscillator.frequency.value = 880;
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
            oscillator.connect(gain).connect(audioCtx.destination);
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.4);
        } catch (e) {
            // Web Audio unavailable/blocked — fail silently, the visual countdown still works.
        }
    }

    function activeStartTimestamp() {
        if (summary.status === "running" && summary.current_session_start) return summary.current_session_start;
        if (summary.status === "on_break" && summary.current_break_start) return summary.current_break_start;
        return null;
    }

    function renderStateGroups() {
        stateGroups.forEach((el) => {
            el.classList.toggle("d-none", el.dataset.stateGroup !== summary.status);
        });
        if (breakStartWrap) breakStartWrap.classList.toggle("d-none", summary.status === "on_break");

        // Collapse the "start something else" panel whenever we're not paused, so it's
        // always freshly collapsed the next time Paused is (re-)entered.
        if (summary.status !== "paused" && startSomethingElseWrap && toggleStartSomethingElse) {
            startSomethingElseWrap.classList.add("d-none");
            toggleStartSomethingElse.innerHTML = 'Start a different activity instead <i class="bi bi-chevron-down"></i>';
        }
    }

    function renderStatCards() {
        document.getElementById("stat-goal").textContent = formatMinutesHM(summary.goal_minutes);
        document.getElementById("stat-completed").textContent = formatMinutesHM(summary.completed_minutes);
        document.getElementById("stat-missed").textContent = formatMinutesHM(summary.missed_minutes);
        document.getElementById("stat-break").textContent = formatMinutesHM(summary.break_minutes);
        document.getElementById("stat-waste").textContent = formatMinutesHM(summary.waste_minutes);
        document.getElementById("stat-total-tracked").textContent = formatMinutesHM(summary.total_unslept_minutes);

        goalProgressBar.style.width = Math.min(100, summary.completion_percent) + "%";
    }

    function renderResumeLabel() {
        const resumeName = document.getElementById("resume-activity-name");
        if (resumeName) resumeName.textContent = summary.last_activity || "";
    }

    function renderBreakCountdown() {
        if (summary.status !== "on_break" || !summary.current_break_start || !summary.current_break_planned_minutes) {
            if (breakCountdown) breakCountdown.textContent = "";
            return;
        }

        const elapsed = (Date.now() - new Date(summary.current_break_start).getTime()) / 1000;
        const plannedSeconds = summary.current_break_planned_minutes * 60;
        const remaining = plannedSeconds - elapsed;

        if (remaining > 0) {
            breakCountdown.textContent = `Break ends in ${formatHMS(remaining)}`;
            breakCountdown.className = "mb-3 fw-semibold";
            if (remaining <= 10 && !hasAlertedThisBreak) {
                hasAlertedThisBreak = true;
                playBeep();
            }
        } else {
            breakCountdown.textContent = `Break time's up — over by ${formatHMS(-remaining)}`;
            breakCountdown.className = "mb-3 fw-semibold text-danger";
        }
    }

    function tick() {
        const meta = STATUS_META[summary.status] || STATUS_META.idle;
        statusBadge.textContent = meta.label;
        statusBadge.className = "badge rounded-pill px-3 py-2 mb-3 " + meta.badgeClass;

        const startIso = activeStartTimestamp();

        if (startIso) {
            const elapsed = (Date.now() - new Date(startIso).getTime()) / 1000;
            elapsedDisplay.textContent = formatHMS(elapsed);
            elapsedLabel.textContent =
                summary.status === "running" ? `Focusing on ${summary.current_activity || "—"}` : "On a break";
        } else {
            elapsedDisplay.textContent = "00:00:00";
            elapsedLabel.textContent = summary.status === "paused" ? "Paused" : "Nothing running";
        }

        renderBreakCountdown();
    }

    function applySummary(newSummary) {
        const wasOnBreak = summary.status === "on_break";
        summary = newSummary;
        if (!wasOnBreak && summary.status === "on_break") hasAlertedThisBreak = false;
        renderStateGroups();
        renderStatCards();
        renderResumeLabel();
        tick();
    }

    function populateTopics(selectEl, subjectId, selectedTopicId) {
        selectEl.innerHTML = "";
        const topics = topicsBySubject[subjectId] || [];

        if (!subjectId) {
            selectEl.appendChild(new Option("-- Select a subject first --", ""));
            selectEl.disabled = true;
            return;
        }

        if (!topics.length) {
            selectEl.appendChild(new Option("-- No topics under this subject --", ""));
            selectEl.disabled = true;
            return;
        }

        selectEl.appendChild(new Option("-- None --", ""));
        topics.forEach((topic) => selectEl.appendChild(new Option(topic.title, topic.id)));
        selectEl.disabled = false;

        if (selectedTopicId) selectEl.value = selectedTopicId;
    }

    function wireSubjectTopic(subjectSelectId, topicSelectId) {
        const subjectSelect = document.getElementById(subjectSelectId);
        const topicSelect = document.getElementById(topicSelectId);
        if (!subjectSelect || !topicSelect) return;

        subjectSelect.addEventListener("change", () => {
            populateTopics(topicSelect, subjectSelect.value, null);
        });
    }

    wireSubjectTopic("subject-select", "topic-select");
    wireSubjectTopic("subject-select-paused", "topic-select-paused");

    if (toggleStartSomethingElse && startSomethingElseWrap) {
        toggleStartSomethingElse.addEventListener("click", (e) => {
            e.preventDefault();
            const expanded = !startSomethingElseWrap.classList.contains("d-none");
            startSomethingElseWrap.classList.toggle("d-none", expanded);
            toggleStartSomethingElse.innerHTML = expanded
                ? 'Start a different activity instead <i class="bi bi-chevron-down"></i>'
                : 'Hide <i class="bi bi-chevron-up"></i>';
        });
    }

    // Toggles the Subject/Topic "required" markers and the Others free-text box based on the
    // selected activity's kind — Study requires subject+topic, Others requires the note.
    function wireActivityKind(activitySelectId, requiredMarkIds, othersWrapId) {
        const activitySelect = document.getElementById(activitySelectId);
        const othersWrap = document.getElementById(othersWrapId);
        if (!activitySelect) return;

        const update = () => {
            const selectedOption = activitySelect.options[activitySelect.selectedIndex];
            const kind = selectedOption ? selectedOption.dataset.kind : "";

            requiredMarkIds.forEach((id) => {
                const mark = document.getElementById(id);
                if (mark) mark.classList.toggle("d-none", kind !== "study");
            });

            if (othersWrap) othersWrap.classList.toggle("d-none", kind !== "others");
        };

        activitySelect.addEventListener("change", update);
        update();
    }

    wireActivityKind("activity-select", ["subject-required-mark", "topic-required-mark"], "others-note-wrap");
    wireActivityKind("activity-select-paused", [], "others-note-wrap-paused");

    function postJson(url, body) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
            body: JSON.stringify(body || {}),
        }).then((response) =>
            response.json().then((data) => ({ ok: response.ok, status: response.status, data }))
        );
    }

    function handleResponse(result, warningEl) {
        if (result.data.ok === false) {
            if (warningEl) {
                warningEl.textContent = result.data.error || "Something went wrong.";
                warningEl.classList.remove("d-none");
            }
            return false;
        }
        if (warningEl) warningEl.classList.add("d-none");
        if (result.data.summary) applySummary(result.data.summary);
        return true;
    }

    function startSession(activitySelectId, subjectSelectId, topicSelectId, othersNoteId, warningEl) {
        const activitySelect = document.getElementById(activitySelectId);
        const activityId = activitySelect.value;

        if (!activityId) {
            warningEl.textContent = "Select an activity first.";
            warningEl.classList.remove("d-none");
            return;
        }

        const kind = activitySelect.options[activitySelect.selectedIndex].dataset.kind;
        const subjectId = document.getElementById(subjectSelectId).value || null;
        const topicId = document.getElementById(topicSelectId).value || null;
        const othersNoteEl = document.getElementById(othersNoteId);
        const notes = othersNoteEl ? othersNoteEl.value.trim() : "";

        if (kind === "study" && (!subjectId || !topicId)) {
            warningEl.textContent = "Select a Subject and Topic to start a Study session.";
            warningEl.classList.remove("d-none");
            return;
        }

        if (kind === "others" && !notes) {
            warningEl.textContent = "Describe what you're doing to start an Others session.";
            warningEl.classList.remove("d-none");
            return;
        }

        postJson("/timer/session/start/", {
            activity_id: activityId,
            subject_id: subjectId,
            topic_id: topicId,
            notes: notes,
        }).then((result) => {
            if (handleResponse(result, warningEl) && othersNoteEl) othersNoteEl.value = "";
        });
    }

    document.getElementById("btn-start").addEventListener("click", () => {
        startSession("activity-select", "subject-select", "topic-select", "others-note", document.getElementById("start-warning"));
    });

    document.getElementById("btn-start-new").addEventListener("click", () => {
        startSession(
            "activity-select-paused",
            "subject-select-paused",
            "topic-select-paused",
            "others-note-paused",
            document.getElementById("start-warning-paused")
        );
    });

    document.getElementById("btn-pause").addEventListener("click", () => {
        postJson("/timer/session/pause/").then((result) => handleResponse(result));
    });

    document.getElementById("btn-resume").addEventListener("click", () => {
        postJson("/timer/session/resume/").then((result) => handleResponse(result));
    });

    document.getElementById("btn-stop-running").addEventListener("click", () => {
        if (confirm("Stop tracking for now? You can start a new session anytime.")) {
            postJson("/timer/session/stop/").then((result) => handleResponse(result));
        }
    });

    document.getElementById("btn-stop-paused").addEventListener("click", () => {
        if (confirm("Stop for the day?")) {
            postJson("/timer/session/stop/").then((result) => handleResponse(result));
        }
    });

    document.getElementById("break-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const reasonInput = document.getElementById("break-reason");
        const minutesInput = document.getElementById("break-minutes");

        if (!reasonInput.value.trim()) {
            alert("A reason is required to start a break.");
            return;
        }
        if (!minutesInput.value || Number(minutesInput.value) < 1) {
            alert("Enter how many minutes your break will be.");
            return;
        }

        postJson("/timer/break/start/", {
            reason: reasonInput.value.trim(),
            planned_minutes: Number(minutesInput.value),
        }).then((result) => {
            if (handleResponse(result)) {
                reasonInput.value = "";
                minutesInput.value = "";
            }
        });
    });

    document.getElementById("btn-end-break").addEventListener("click", () => {
        postJson("/timer/break/end/").then((result) => handleResponse(result));
    });

    function pollSummary() {
        fetch("/timer/summary/")
            .then((response) => response.json())
            .then((data) => applySummary(data))
            .catch(() => {});
    }

    setInterval(tick, 1000);
    setInterval(pollSummary, 5000);

    applySummary(summary);
})();
