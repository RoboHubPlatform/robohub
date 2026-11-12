# Changelog

## [0.1.0] - 2026-11-04

The Mesh provider for the gateway contract: projects, a project's gateway,
sources, device states and a source's state.

## [0.1.1] - 2026-11-04

The provider sends the gateway service token on Mesh requests, so protected Mesh APIs accept its reads and actions.

## [0.2.0] - 2026-11-05

The provider serves Mesh telemetry: a source's newest reading, a time-range
series and the store status. A source may be named by ID, by the value or action
URL a widget stored, or by a URL carrying `source=`; the provider extracts the
ID and asks `/mesh/api/projects/{project}/telemetry/series`.

## [0.2.1] - 2026-11-06

Provider now resolves source IDs from URLs, value URLs, and source= params.
Latest and history calls work with any stored form.

## [0.2.2] - 2026-11-12

The provider declares `rho-log`, which it imports, and calls the language's string functions rather than runtime functions its includer had to declare.

## [0.3.0] - 2026-11-12

A provider of the gateway interface: it lists `robohub.gateway` under
`implements`, exports the interface's functions by their own names, and reads
Mesh's address and the project from the application's binding (`url`,
`project`). The `provider:` block, the configuration string each function took,
and the contract helpers it borrowed are gone.
