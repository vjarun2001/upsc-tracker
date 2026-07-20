(function () {
    const STORAGE_KEY = "pomodoro_state_v1";
    const ALARM_LEAD_SECONDS = 10;

    let audioCtx = null;
    let tickListeners = [];
    let completeListeners = [];
    let lastAlarmSecond = null;

    function ensureAudioContext() {
        if (!audioCtx) {
            const Ctor = window.AudioContext || window.webkitAudioContext;
            if (!Ctor) return null;
            audioCtx = new Ctor();
        }
        if (audioCtx.state === "suspended") {
            audioCtx.resume();
        }
        return audioCtx;
    }

    function beep(freq, duration, delay, volume) {
        const ctx = ensureAudioContext();
        if (!ctx) return;

        const startAt = ctx.currentTime + (delay || 0);
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.frequency.value = freq;
        osc.type = "sine";
        gain.gain.setValueAtTime(0, startAt);
        gain.gain.linearRampToValueAtTime(volume || 0.25, startAt + 0.02);
        gain.gain.linearRampToValueAtTime(0, startAt + duration / 1000);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(startAt);
        osc.stop(startAt + duration / 1000 + 0.05);
    }

    function playAlarmTick() {
        beep(880, 120, 0, 0.2);
    }

    function playCompletionChime() {
        beep(660, 160, 0, 0.3);
        beep(880, 160, 0.18, 0.3);
        beep(1046, 260, 0.36, 0.3);
    }

    function notify(title, body) {
        if (!("Notification" in window)) return;

        function fire() {
            try {
                new Notification(title, { body: body });
            } catch (e) {
                /* ignore */
            }
        }

        if (Notification.permission === "granted") {
            fire();
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(function (perm) {
                if (perm === "granted") fire();
            });
        }
    }

    function loadState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function saveState(state) {
        if (state) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    }

    function remainingSeconds(state) {
        if (!state) return 0;
        if (state.paused) return state.remainingAtPause;
        return Math.max(0, Math.round((state.endAt - Date.now()) / 1000));
    }

    function start({ sessionType, totalSeconds, taskId, subjectId, topicId }) {
        ensureAudioContext();
        lastAlarmSecond = null;

        const state = {
            sessionType: sessionType,
            totalSeconds: totalSeconds,
            endAt: Date.now() + totalSeconds * 1000,
            paused: false,
            remainingAtPause: null,
            taskId: taskId || null,
            subjectId: subjectId || null,
            topicId: topicId || null,
        };

        saveState(state);
        renderWidget();
    }

    function pause() {
        const state = loadState();
        if (!state || state.paused) return;

        state.remainingAtPause = remainingSeconds(state);
        state.paused = true;
        saveState(state);
        renderWidget();
    }

    function resume() {
        const state = loadState();
        if (!state || !state.paused) return;

        state.endAt = Date.now() + state.remainingAtPause * 1000;
        state.paused = false;
        state.remainingAtPause = null;
        saveState(state);
        renderWidget();
    }

    function stop() {
        const state = loadState();
        if (!state) return null;

        const elapsed = state.totalSeconds - remainingSeconds(state);

        if (elapsed > 0) {
            logSession(state, elapsed, false);
        }

        saveState(null);
        removeWidget();
        return state;
    }

    function logSession(state, actualSeconds, isCompleted) {
        if (!window.POMODORO_LOG_URL) return;

        fetch(window.POMODORO_LOG_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                session_type: state.sessionType,
                planned_duration_minutes: Math.round(state.totalSeconds / 60),
                actual_duration_seconds: actualSeconds,
                is_completed: isCompleted,
                task: state.taskId || null,
                subject: state.subjectId || null,
                topic: state.topicId || null,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                completeListeners.forEach(function (cb) {
                    cb(data, state);
                });
            })
            .catch(function () {});
    }

    function removeWidget() {
        const el = document.getElementById("pomodoro-floating-widget");
        if (el) el.remove();
    }

    function isOnTimerPage() {
        return !!document.getElementById("timer-display");
    }

    function renderWidget() {
        if (isOnTimerPage()) {
            removeWidget();
            return;
        }

        const state = loadState();
        if (!state) {
            removeWidget();
            return;
        }

        let el = document.getElementById("pomodoro-floating-widget");
        if (!el) {
            el = document.createElement("div");
            el.id = "pomodoro-floating-widget";
            el.className = "pomodoro-floating-widget";
            el.innerHTML =
                '<a href="/planner/pomodoro/" class="pomodoro-floating-link">' +
                '<i class="bi bi-stopwatch"></i> ' +
                '<span class="pomodoro-floating-type"></span> ' +
                '<span class="pomodoro-floating-time"></span>' +
                "</a>";
            document.body.appendChild(el);
        }

        const remaining = remainingSeconds(state);
        const minutes = Math.floor(remaining / 60).toString().padStart(2, "0");
        const seconds = (remaining % 60).toString().padStart(2, "0");
        const typeLabel = state.sessionType === "focus" ? "Focus" : "Break";

        el.querySelector(".pomodoro-floating-type").textContent = typeLabel;
        el.querySelector(".pomodoro-floating-time").textContent =
            (state.paused ? "⏸ " : "") + minutes + ":" + seconds;
    }

    function tick() {
        const state = loadState();

        if (!state) {
            lastAlarmSecond = null;
            return;
        }

        if (state.paused) {
            renderWidget();
            tickListeners.forEach(function (cb) {
                cb(state, remainingSeconds(state));
            });
            return;
        }

        const remaining = remainingSeconds(state);

        if (remaining <= 0) {
            playCompletionChime();
            notify(
                "UPSC Tracker",
                (state.sessionType === "focus" ? "Focus" : "Break") + " session complete!"
            );
            logSession(state, state.totalSeconds, true);
            saveState(null);
            lastAlarmSecond = null;
            removeWidget();

            tickListeners.forEach(function (cb) {
                cb(null, 0);
            });
            return;
        }

        if (remaining <= ALARM_LEAD_SECONDS && remaining !== lastAlarmSecond) {
            lastAlarmSecond = remaining;
            playAlarmTick();
        }

        renderWidget();

        tickListeners.forEach(function (cb) {
            cb(state, remaining);
        });
    }

    document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible") {
            tick();
        }
    });

    setInterval(tick, 1000);
    tick();

    window.PomodoroCore = {
        start: start,
        pause: pause,
        resume: resume,
        stop: stop,
        getState: loadState,
        remainingSeconds: function () {
            return remainingSeconds(loadState());
        },
        onTick: function (cb) {
            tickListeners.push(cb);
        },
        onComplete: function (cb) {
            completeListeners.push(cb);
        },
        unlockAudio: ensureAudioContext,
    };
})();
