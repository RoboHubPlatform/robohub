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

## [0.4.0] - 2026-11-13

Implements robohub-gateway 1.1.0. `action` posts to the source's action path
with the project-scoped service token. A `transport` setting (`auto`, `bus`,
`http`; `auto` by default) chooses how `follow` gets the live stream: over the
broker, from Mesh's relayed `mesh/<project>/telemetry` topic, when the
installation has one (`ROBOHUB_BUS_*`) — or from Mesh's HTTP stream otherwise.
Both write the same lines, so the application reads one file either way. The
data directory the answers are written to is made once, not by a `mkdir`
child process on every request.

## [0.5.0] - 2026-11-13

Implements robohub-gateway 1.2.0's `nodes()`, from Mesh's
`/mesh/api/projects/<project>/nodes` (Mesh 0.18).

## [0.5.1] - 2026-11-13

A reading is returned as the response body (`rho_http_body`, rho 0.6.0) instead of through one `mesh-source-latest` file every caller shared: a page and the background loop asking at once could be handed each other's reading, so a load's switch could read another source's value. A source id in a URL is encoded, including `%`, `#` and `+`, and a value ending in a line break is trimmed ("on\n" is "on").

## [0.5.2] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A query value escapes every reserved byte, and a line break is escaped rather than dropped.

## [0.5.3] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Copies of helpers the toolchain now provides (`i64_to_str`, `str_lower`, `str_field`, `json_str_field`, `escape_html`) are gone. Needs rho 0.8.0.

## [0.5.4] - 2026-11-14

`token` is no longer listed among its settings: it never read one (every request carries a service token from the issuer). A `bind.conf` that still has the line is unaffected; the line is ignored.
