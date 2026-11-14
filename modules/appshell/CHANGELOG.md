# Changelog

All notable changes to this module are recorded here, one section per release.

## [0.1.0] - 2026-11-13

The settings page, the docs page and the shell's pieces — rail links, the top
bar with where readings come from and the mode in force, a toast — that the
aquarium and energy each carried a copy of. An application includes the
module, keeps its own rail, top-bar action and layout, and answers host_app()
and host_app_title(). The module serves `/settings` and `/docs`.

## [0.1.1] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0.

## [0.1.2] - 2026-11-14

The settings page knows no module's settings: its tabs are the gateway, the ones the application adds for its modules (`host_settings_tabs`, `host_settings_form`, `host_settings_save`) and logging and about, and each module draws and keeps its own form. The bar is drawn in the request's language.
