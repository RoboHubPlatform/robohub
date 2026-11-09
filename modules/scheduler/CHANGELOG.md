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
