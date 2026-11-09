# Scheduler

A reusable module for recurring maintenance and deferred actions. It registers
its routes on the host application's router under `/scheduler`; it has no port
of its own.

## Host shell

The module registers `/scheduler`, but it renders content only. Its pages call
the host's `host_shell(req, title, body, scripts)`, so the application owns the
header, footer and menu. The scheduler CSS travels in
`templates/parts/style.html` with the content, keeping the tabs, due badges and
chore controls intact in aquarium and energy alike.

## Schedules

- **Interval** — every N hours.
- **Cron** — the daily `M H * * *` and weekly `M H * * D` forms.
- **One time** — a date and time in the future.
- **Usage** — after N hours of use, fed by `POST /api/scheduler/chores/{id}/usage`.

A chore can have a grace period; when it reaches zero it is **due**, and after
the grace it is **overdue**. Completing it records the note and computes the
next due time immediately. Snoozing moves the visible due time without changing
the schedule.

## API

| Method | Path | Meaning |
|--------|------|---------|
| `GET` | `/api/scheduler/chores` | chores with status and due time |
| `POST` | `/api/scheduler/chores` | create a chore |
| `POST` | `/api/scheduler/chores/{id}/complete` | complete with an optional note |
| `POST` | `/api/scheduler/chores/{id}/snooze` | snooze in hours |
| `POST` | `/api/scheduler/chores/{id}/usage` | add runtime hours |

## Storage

The module owns its tables, not their location. The host application's main SQL
database is where they live (`$ROBOHUB_APP_WORKSPACE/data/app.db`), and the host
declares the module instance and its SQL files in `app_modules`. Two applications
including the scheduler have separate databases.
