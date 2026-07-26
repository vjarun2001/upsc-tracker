# Time Tracker

A time-audit system, not a countdown timer: each day gets a fixed minutes
budget — **"Daily Unslept Hours"** (`DailyTimer.goal_minutes`, snapshotted
from `Profile.daily_study_target_minutes` at creation) — and the user logs
open-ended sessions against `Activity` categories. Every user gets 4 default
Activities (`Study`, `Tuition`, `Break`, `Others`), classified by
`Activity.kind`, which drives extra mandatory fields at Start:

- **Study** — requires a Subject + Topic. Time logged against a nested topic
  (e.g. Calculus, a child of Algebra) rolls up into every ancestor topic and
  the Subject total on the Syllabus page (`apps/study/services.py::topic_minutes_with_descendants`).
- **Tuition** — a plain activity, no mandatory fields.
- **Break** — requires a reason and a planned duration (minutes). See below.
- **Others** — requires a free-text note (`TimerSession.notes`, set at
  creation, not just editable post-close).

User-created custom Activities always get `kind=CUSTOM` (no special fields) —
`ActivityForm` never exposes `kind`, so a user renaming e.g. "Study" to "My
Studies" doesn't lose the Subject/Topic requirement (it's driven by `kind`,
not `name`).

## Break and Wasted time are one flow, not two

There is no more manual "start/stop tracking a distraction" action. Wasted
time is entirely **derived** from how long a break actually took versus its
planned duration:

1. `start_break(reason, planned_minutes)` — both mandatory. A client-side
   countdown (and a synthesized alert beep in the last ~10 seconds) tells the
   user their planned time is running out.
2. `end_break()` — whenever the user actually clicks Resume/Start-new,
   however early or late: `_maybe_log_break_overrun()` computes
   `max(actual_duration - planned_minutes*60, 0)`. If positive, that overrun
   is logged as a `WasteSession` (auto-created, already-closed — reusing the
   existing model/`DailySummary.waste_minutes`/Timeline-event machinery
   unchanged; only its *creation path* moved from a manual button to this one
   call site). Returning on time or early logs zero wasted time.

A break left open overnight (device closed, app not reopened) still gets this
same overrun computation applied during rollover, at the same 23:59:59 force-close.

## State machine

Exactly one of `{RUNNING, ON_BREAK}` can be true at a time (no separate
"wasting" state — see above). `PAUSED` is the hub between sessions and breaks.

| From | Action | To |
|---|---|---|
| IDLE, PAUSED | `start_session(activity, subject=None, topic=None, notes="")` | RUNNING |
| RUNNING | `pause_session()` | PAUSED |
| PAUSED | `resume_session()` (reuses last session's activity/subject/topic/notes) | RUNNING |
| RUNNING, PAUSED | `stop_session()` | IDLE |
| RUNNING | `start_break(reason, planned_minutes)` (implicitly closes the open session) | ON_BREAK |
| IDLE, PAUSED | `start_break(reason, planned_minutes)` | ON_BREAK |
| ON_BREAK | `end_break()` (may auto-log overrun as Wasted time) | PAUSED |
| any non-CLOSED | rollover / explicit end-day | CLOSED |

Illegal transitions (including missing mandatory reason/duration/subject/topic/notes)
raise `services.TimerStateError`; views translate it to a `409` JSON response.

`TimerSession`/`BreakSession`/`WasteSession` rows are immutable once closed
(only `notes` may still change post-close, though for `Others` it's already
set at creation) — "pause closes the row; resume opens a new one," so a
session's start/end/duration is never edited in place.

## Concurrency

Enforced at the DB level, not just in the service layer: each of
`TimerSession`, `BreakSession` has a
`UniqueConstraint(fields=["daily_timer"], condition=Q(end_at__isnull=True))` —
at most one open row of each kind per day, even under a double-click or a
two-tab race. `WasteSession` never has an open row anymore (always created
already-closed). `DailyTimer`'s `unique_together("user", "date")` is the
per-day lock. Every service function wraps its check-then-write in
`transaction.atomic()`.

## Midnight rollover

There is no scheduled-job infrastructure in this project (no Celery/cron), so
rollover is lazy/JIT: `services.get_or_open_daily_timer(user)` runs at the top
of every timer-touching view and does the rollover check inline, in the same
transaction, before returning today's row.

1. If today's `DailyTimer` already exists and isn't `CLOSED`, return it
   (fast path).
2. Otherwise, find every non-`CLOSED` `DailyTimer` with `date != today`,
   oldest first (self-heals multi-day gaps, e.g. the app wasn't opened for a
   few days).
3. For each stale day: force-close any open session/break at `23:59:59`
   local time *of that day* (not "whenever this check happens to run" — caps
   a forgotten open tab at a sane duration), applying the same break-overrun
   check described above; write the matching `*_ENDED` + `DAY_CLOSED`
   `TimerEvent` rows, mark `status=CLOSED`, set `closed_at=now()` (the real
   wall-clock rollover time, for audit), and generate its `DailySummary`
   (`update_or_create`, idempotent).
4. Create today's `DailyTimer` (`status=IDLE`, goal snapshotted from the
   user's profile) and a `DAY_STARTED` event.

`DailySummary` is only ever persisted for closed/past days — "today" is
always computed live via `services.today_summary()` so it can't go stale
while the day is still in progress. `services.historical_range_summary()`
(used by `/timer/history/`) reads `DailySummary` for past days in a range and
falls back to `today_summary()` for today if it falls inside that range.

## Default Activity seeding

Every user gets `Study`/`Tuition`/`Break`/`Others` automatically:
- **New signups**: `apps/timetracker/signals.py::create_default_activities`
  (`post_save` on `User`, `if created:` guard — same pattern as
  `apps/accounts/signals.py::create_profile` and
  `apps/tracker/signals.py::create_default_trackers`).
- **Existing users** (retroactive backfill, since this project has no other
  precedent for it): a one-time `RunPython` data migration
  (`apps/timetracker/migrations/0003_seed_default_activities.py`), using
  `get_or_create` — safe against a user who'd already self-created a
  same-named Activity (it upgrades that row's `kind` in place rather than
  erroring on the `unique_together("user","name")` constraint or leaving it
  un-classified).

## Seeding sample data

```
python manage.py seed_timetracker --email you@example.com --days 14
```

Creates the standard UPSC-prep Activity set (GS1-4, Optional, CSAT,
Newspaper, Revision, etc.) and a mix of goal-met/missed/no-activity days over
the requested window, for local demoing. Skips any day that already has a
`DailyTimer`, so it's safe to re-run.

## Tests

`python manage.py test apps.timetracker` — covers default-Activity seeding,
the state machine (legal/illegal transitions, mandatory Study/Others/Break
fields), break-overrun-as-wasted-time (on-time/early returns log nothing,
late returns log the correct overrun, including at rollover for a break left
open overnight), DB-level concurrency (`IntegrityError` on a
second open row), the rollover algorithm (stale-day force-close + summary
generation), `today_summary`/`activity_stats`/`historical_range_summary`
aggregation, and Activity CRUD (archive vs. protected hard-delete).
