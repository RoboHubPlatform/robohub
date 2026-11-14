# Scheduler

Recurring maintenance and deferred actions — chores — for a host application:
a water change every week, a filter rinse after 720 hours of running, a check at
a set time. The module registers its pages and API on the host's router
(`/scheduler`, `/api/scheduler/...`); it has no port of its own. Aquarium and
energy include it.

## How an application uses it

Include the module and add it to `deps`. It brings `i18n`, `settings`,
`notifications`, `forms` and `inventory`.

The application:

- defines `host_shell(req, title, body, scripts)`: the module's pages render
  content only, and their CSS travels with the content;
- seeds its chores at startup with `scheduler_presets(text)` (below);
- calls `scheduler_usage_tick()` from its background work, after
  `inventory_runtime_tick()`, if chores follow an item's runtime;
- calls `scheduler_complete_title(title, note)` when what it records is the
  chore itself — a water change logged is the water-change chore done;
- adds the module's settings tab: `scheduler_settings_form` and
  `scheduler_settings_save`, combined through `host_settings_tabs/form/save`
  (see {ref}`appshell/index`).

`scheduler_status(chore, now)` and `scheduler_links_text(chore)` let an
application show a chore's state and what it is tied to on its own pages.

## Schedules

| Kind | When it is due |
|---|---|
| `interval` | Every N hours (`interval_hours`; a day when none is given) |
| `cron` | A five-field cron expression (minute, hour, day of month, month, day of week) in the machine's local time: `*`, `5`, `1-5`, `1,3,5`, `*/15`, `10-50/20`. As in cron, when both day fields are restricted a day matching either is taken; day of week 7 is Sunday |
| `one_time` | A date and time |
| `usage` | After N hours of use (`usage_hours`), typed in, posted to `POST /api/scheduler/chores/{id}/usage`, or counted from an inventory item's runtime |

A chore is **due** when its time comes and **overdue** once its grace period
(`grace_hours`) has passed. Completing it records the note and computes the next
due time at once. Snoozing moves the visible due time without changing the
schedule.

## Tied to the inventory

A chore can name inventory items by handle. `runtime_of: filter-main` makes a
usage chore count the item's switch runtime instead of hours typed in; only
runtime gained since the chore was tied to the item counts. `consumes:
filter-pads` with `consumes_qty: 1` takes that much off the shelf each time the
chore is done, recorded as a stock movement for the chore (`chore#<id>`).

## Presets

`scheduler_presets(text)` seeds the chores from the text of the application's
`presets/schedule.yml`. Each chore under `chores:` has a `title` and a `kind`,
and may have `value` (the cron expression or the date), `interval_hours`,
`usage_hours`, `grace_hours`, `priority`, `runtime_of`, `consumes` and
`consumes_qty`:

```yaml
chores:
  water-change:
    title: Water change 30 %
    kind: interval
    interval_hours: 168
  rinse-filter:
    title: Rinse filter media
    kind: usage
    usage_hours: 720
    runtime_of: filter-main
    consumes: filter-pads
    consumes_qty: 1
```

A chore is added once, by its title; after that it is the person's.

## API

The JSON API under `/api/scheduler/chores` lists chores with their status and
due time, creates one, and completes, snoozes (in hours) or adds usage hours to
one by id. The routes are listed in the reference below.

## Settings

Kept in the application's settings store (see {ref}`settings/index`):

| Key | Default | What it is |
|---|---|---|
| `scheduler.grace_hours` | `12` | The grace period a new chore starts with |
| `scheduler.priority` | `normal` | The priority a new chore starts with |

## Data it keeps

In the application's database, `<workspace>/data/app.db` (or
`RHO_SCHEDULER_DB`), from the module's own `db/schema.sql`, which rho-sql
generates into every application that depends on the module:

| Table | What it holds |
|---|---|
| `chores` | Each chore: its schedule, next due time, grace, priority, and what it is tied to in the inventory (`runtime_of`, the runtime already counted, `consumes`) |
| `chore_completions` | Each completion, with the note a person left |

Additions and completions are written to the application log under the
`scheduler` subject; a changed chore is written to the journal.
