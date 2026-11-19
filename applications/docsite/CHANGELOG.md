# Changelog

All notable changes to this module are recorded here, one section per release.

## [0.2.0] - 2026-11-01

Each module's page now carries its release history: the module's
`CHANGELOG.md` is appended below its documentation when the site is assembled.
The site identity reports the docsite's own version (0.2.0).

## [0.3.0] - 2026-11-02

The site now collects applications, modules and plugins as well as the
ecosystem registry. Each application, module and plugin has its own page, and
the orchestrator's index links to them under Applications, Modules and Plugins.

## [0.3.1] - 2026-11-03

A module's documentation is copied with its images, so a page that shows a
screenshot carries it into the assembled site.

## [0.3.2] - 2026-11-04

The site has a landing page in the Rho docsite style: an overview of the
ecosystem, links to the documentation and the main applications, the repository,
and the current release. Release histories in module pages preserve the
changelog line breaks.

## [0.3.3] - 2026-11-04

Module release histories preserve changelog paragraphs consistently, and the
landing page lists the five most recent releases sorted by version.

## [0.3.4] - 2026-11-04

The landing release history now shows the full changelog note for each
release, not only its first line.

## [0.3.5] - 2026-11-04

Landing and module changelogs both preserve line breaks, shown as line breaks
rather than one wrapped block.

## [0.3.6] - 2026-11-04

Landing and module changelogs use the same paragraph extraction: wrapped source
lines are joined into paragraphs, so there are no half-empty lines and spacing
is consistent.

## [0.3.7] - 2026-11-08

The site now carries the reactive UI, i18n, settings, telemetry, OTA and
provisioning documentation, and the RoboHub 0.4.0 release notes.

## [0.3.8] - 2026-11-14

Its own replace helper is gone for the toolchain's `str_replace` (rho 0.8.3), which it needs.

## [0.3.9] - 2026-11-19

The assembled tree named the parts nested in robohub by their folders (`alert`, `email`, `gateway`) while `rho req` names them by their `requirements: name:` or module name (`robohub-alert`, `robohub-provider-email`, `robohub-gateway-contract`), so the tree's parts were not the repositories' parts and a qualified reference to one did not resolve; and it copied the gateway contract twice (through the contracts folder and again renamed). Each nested part is now one folder named as `rho req` names it (`templates/scripts/part-name.awk`), its manifest renamed when that differs from its module name; `rho req check --workspace` on the tree is clean and finds the same parts as in the repositories (`tests/tree_names.sh`). The program read its tree argument from the wrong position (`rho_arg(1)`, the second argument), so `docsite <tree>` silently used `build/doctree`; it reads `docsite [tree] [site]` now, the site folder included, so a check can leave `build/site` alone.
