# Changelog

## [0.1.0] - 2026-11-08

First release. Adds the host-owned key-value settings store used by applications
and their modules.

## [0.1.1] - 2026-11-12

The store also follows `RHO_APP_WORKSPACE`, the name the keeper gives an
application's workspace, so an application started with only that one keeps its
settings to itself instead of sharing the fallback store.
