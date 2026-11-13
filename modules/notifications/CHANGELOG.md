# Changelog

## [0.1.1] - 2026-11-08

Live notification events carry a locale, the embed filters by the page language,
and the default toast text is available in English and Romanian. Alert log
writes remain file-based.

## [0.1.2] - 2026-11-09

The module's clock file is written under the application workspace instead of
the module source tree, so running an application no longer changes a tracked
file in `modules/notifications`. Every pushed notification is also written to
the host application log.

## [0.1.3] - 2026-11-12

The module declares the runtime functions it calls, and reading the outcome of a command uses its own trim rather than the including application's.

## [0.1.4] - 2026-11-13

A notification's level is escaped where it becomes part of a class attribute.

## [0.1.5] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once.
