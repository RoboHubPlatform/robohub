# Changelog

All notable changes to this module are recorded here, one section per release.

## [0.1.0] - 2026-11-13

The RoboHub look as a module: design tokens for a dark and a light theme (the same
variables, so a theme changes colours and nothing else), the components every
application draws — cards with one pill, chips, the inspector with its tabs, rows,
the "applying this change" box, the strip — the top bar with the app switcher and
the person's menu, and the theme a person chooses kept in a cookie every
application on the host reads.

## [0.1.1] - 2026-11-13

An application that is not the keeper draws the same top bar (`ui_topbar_remote`):
its switcher fills itself from the keeper's `/api/v1/switcher`. The person's menu
can leave the theme out for an application that has no light look yet, takes its
sign-out as HTML (an application signs out at the keeper), and the language choice
is shared (`ui_language`). An inspector can be a page of its own (`rh-ins-page`,
with `rh-crumbs` above it), and its tabs no longer collapse when its body is tall.

## [0.1.2] - 2026-11-13

A browser keeps the stylesheet and the script for five minutes rather than a day,
and the version in their address moves with the module, so a page never runs
with the look of an older release (where an inspector's tabs collapsed under a
long log).

## [0.1.3] - 2026-11-14

The app switcher links to an application through the keeper's origin when the keeper says so (`path` in its switcher list), and to its port otherwise.
