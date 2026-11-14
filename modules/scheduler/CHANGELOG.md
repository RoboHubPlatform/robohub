# Changelog

## [0.1.0] - 2026-11-02

The scheduler module. Interval, cron, one-time and usage-based chores; due and
overdue states with a grace period; completion notes and next-due recalculation;
snoozing; and a JSON chores API under `/api/scheduler/chores`. Tables live in the
host application's main SQL database.

## [0.1.1] - 2026-11-03

The scheduler page carries the same full application menu as the dashboard.

## [0.1.2] - 2026-11-08

English/Romanian navigation and page copy, forms-engine add-chore flow with CSRF,
and scheduler defaults moved to parent settings.

## [0.1.3] - 2026-11-09

Pages render content through the host shell, so the host application owns the header, footer and menu. The scheduler CSS moved into `templates/parts/style.html` with the content. Chore additions and completions are written to the host application log.

## [0.1.4] - 2026-11-12

The module declares the runtime functions it calls rather than relying on helpers the including application defines. Its smoke test signs in with a keeper ticket and sends the form token the module checks.

## [0.1.5] - 2026-11-13

The module declares its tables and statements in its own `sql:` block, and
rho-sql 0.2 generates them into each application that depends on it, so an
application no longer repeats them. The smoke test runs in the aquarium's own
repository.

## [0.2.0] - 2026-11-13

A chore can be tied to the inventory: `runtime_of` names an item whose switch
runtime (counted by inventory 0.2) drives a usage chore through
`scheduler_usage_tick()`, and `consumes` names an item and a quantity that
completing the chore takes off the shelf, recorded as a stock movement for that
chore. An application seeds its chores from its presets (`scheduler_presets`);
a seeded chore is added once and is the person's after that. `scheduler_complete_title(title, note)` completes a chore by its title, for an
application whose own record is the chore (a water change logged).

## [0.2.1] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. A date a person typed is one argument of `date -d`, run without a shell (`rho_exec_capture`), and its answer is returned rather than read from a shared file.

## [0.2.2] - 2026-11-13

Cron is read as cron: `*`, numbers, ranges, lists and steps in all five fields (`*/15 * * * *`, `30 9 * * 1-5`, `0 8 * * 7`), day of week 7 as Sunday, and a day of the month or of the week matching when both are restricted, in local time with the offset of each moment. Before, `*/15` was never due and every weekday range was Saturday. A cron that names no time is refused. The API's add says whether the chore was kept, and why not, instead of always answering 201.

## [0.2.3] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A quantity reads a decimal comma and a sign; a negative one is 0.

## [0.2.4] - 2026-11-14

Cron is read in src/cron.rho, apart from the chores, and has unit tests of its own (tests/scheduler_test.rho): fields, lists, ranges and steps, the next time in local time in any time zone, and expressions that name no time. Nothing it does changed.

## [0.2.5] - 2026-11-14

The route handlers are `scheduler_chores_add`, `scheduler_chores_complete` and so on, and the helpers and constants carry the prefix too (`ignore_string` is `scheduler_ignore_string`); unprefixed, they were in every including application's namespace.

## [0.2.6] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. It declares the i18n module it uses. Needs rho 0.8.0.

## [0.2.7] - 2026-11-14

A chore can be edited — its schedule, what it uses, its priority — and deleted with its history, from its row; renaming one does not move when it is due. The row's forms carry the form token and are translated, and a change returns to the page by GET.

## [0.2.8] - 2026-11-14

Its settings form is its own (`scheduler_settings_form`, `scheduler_settings_save`), shown by an application as one of its settings tabs.
