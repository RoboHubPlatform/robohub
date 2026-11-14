# Reactive UI

RoboHub applications stay server-rendered. HTMX makes a page react to what the
server already knows, and Server-Sent Events (SSE) push live changes. There is no
node runtime, no bundler, and no client-side router to deploy on an edge device.

The shared {ref}`htmx/index` module vendors HTMX and its SSE extension,
serves them from `/assets/`, and carries the small helpers a host uses:

- `htmx_head()` — the two script tags for a layout;
- `htmx_is_request(req)` — whether `HX-Request` is true;
- `htmx_redirect(location)` — a redirect HTMX follows as a page change;
- `htmx_trigger(resp, event)` — dispatch a client event after a swap.

## The rules

1. **One SSE connection per page.** Browsers limit concurrent HTTP/1.1
   connections per origin. Put `hx-ext="sse"` and `sse-connect` on one stable
   wrapper, then route updates with event names. Do not open one EventSource per
   card.
2. **Send a snapshot first.** `sse_events(path, snapshot, interval_ms)` sends the
   snapshot from its start before following the live file. A reconnect sees
   current state instead of waiting for the next change.
3. **Fragments are server-owned HTML.** A handler returns the component, not
   JSON. Use escaped `{{ value }}` for data and `{{{ fragment }}}` only for HTML
   the server built. Never build DOM from JSON in JavaScript.
4. **One response, two clients.** A handler answers a fragment when
   `htmx_is_request(req)` is true and keeps its normal redirect or full page
   otherwise. Forms still work with JavaScript off.
5. **Keep the data plane where it belongs.** Mesh owns the gateway and the
   telemetry store. Aquarium and Energy ask Mesh for data and render their own
   fragments. Do not make telemetry an application UI server.

## A page

```html
<head>
  {{{ htmx }}}
</head>
<body>
  <div id="live" hx-ext="sse" sse-connect="/events">
    <div id="card" sse-swap="card" hx-swap="outerHTML">
      {{{ card }}}
    </div>
  </div>
</body>
```

The layout passes `vars("htmx", htmx_head())` when it fills the page.

## A dual-mode handler

```rho
fn widget_toggle(req: Request) Response {
    let body: string = request_body(req)
    let id: u32 = rho_int_from_str(trim(form_value(body, "id")))
    let card: string = widget_card_html(id)
    if htmx_is_request(req) {
        return html(status_ok(), card)
    }
    return redirect("/widgets")
}
```

The form names the target:

```html
<form method="post" action="/widgets/toggle"
      hx-post="/widgets/toggle"
      hx-target="#widget-{{ id }}" hx-swap="outerHTML">
  <input type="hidden" name="id" value="{{ id }}">
  <button type="submit">Toggle</button>
</form>
```

## A named event stream

The host writes one JSON object per line:

```json
{"event":"card","data":"<div id=\"card\">...</div>"}
```

and serves it with the snapshot file:

```rho
return sse_events(events_file, snapshot_file, 1000)
```

The streamer emits:

```text
event: card
data: <div id="card">...</div>

```

Multi-line HTML is sent as one `data:` line per line. A `__DONE__:` line closes
the stream, which is how a build log ends.

## What still needs JavaScript

HTMX covers actions, swaps and live regions. Keep a small script for behavior
the server cannot express:

- scrolling and clearing a build console;
- clipboard copy;
- a browser confirmation that needs the current DOM value;
- the wizard action runner, which must start a run and follow that run's
  isolated progress file.

Those scripts are the exception, not the page architecture.

## Telemetry

Telemetry belongs to Mesh. Mesh exposes a data-only feed per project at
`/mesh/api/projects/{project}/telemetry/stream`. It emits `telemetry` events whose
data is JSON:

```json
{"project":"default","source":"ba06f37ca34ba32c","area":1,"node":7,
 "field":"temperature","value":"24.5","status":0,"received_ms":1794095053000}
```

The stream starts with the project's current values and then carries changes. An
application does not open it from the browser: its gateway provider follows it on
the server (`gateway.follow`, or the MQTT topic `mesh/<project>/telemetry`), and the
application renders its own fragments from what arrives — see
{ref}`architecture/reading`. Mesh and the gateway stay the only places that reach
drivers and devices.

## Verifying a change

- A request with `HX-Request: true` returns a fragment; a normal request still
  redirects or returns the page.
- `curl -N` on the event endpoint returns named events and a snapshot before
  live changes.
- The page holds one SSE connection, not one per component.
- Forms continue to work with JavaScript disabled.

## Starting a new application

A reactive application keeps the ordinary RoboHub layout and adds three things:
the HTMX dependency, one SSE connection, and fragment responses.

```text
example/
  module.yml
  project.yml
  src/main.rho
  templates/
    layouts/layout.html
    pages/home.html
    parts/notice.html
  static/
```

`module.yml` names the shared module:

```yaml
deps:
  rho-log: ">=0.1.0"
  robohub:
    htmx: ">=0.1.0"
```

`src/main.rho` includes it by name, beside the other modules:

```rho
include "htmx"
```

The layout passes the scripts once:

```html
<head>
  {{{ htmx }}}
</head>
```

```rho
let document: string = template_fill(template_get("layout"),
    vars("title", "Example") + vars("htmx", htmx_head()) + vars("body", body))
```

`project.yml` maps template names to files, and the first route that needs a
fragment answers both clients:

```rho
fn example_toggle(req: Request) Response {
    let card: string = example_card()
    if htmx_is_request(req) {
        return html(status_ok(), card)
    }
    return redirect("/")
}
```

The application owns its `/events` endpoint and its event file. Mesh owns the
gateway and telemetry; the new application asks Mesh for data and renders its own
fragments.

Checklist:

- one `sse-connect` per page;
- snapshot before live events;
- `{{ value }}` for data and `{{{ fragment }}}` for server-built HTML;
- every action keeps a normal POST path;
- assets are served by the HTMX module, not a CDN.

### Languages in live fragments

A shared SSE connection carries one fragment for every client, so a translated
fragment names its language in the event. Widget cards, for example, use
`widget-<id>-en` and `widget-<id>-ro`; the card template subscribes with
`widget-<id>-{{ locale }}`. Data-only feeds such as telemetry stay locale-neutral.

`rho build` reports locale keys that are missing from a non-default catalog, and
keys that the default catalog does not have, so a partial translation is visible
without failing the build.
