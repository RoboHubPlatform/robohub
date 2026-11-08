# Reactive UI

RoboHub applications stay server-rendered. HTMX makes a page react to what the
server already knows, and Server-Sent Events (SSE) push live changes. There is no
node runtime, no bundler, and no client-side router to deploy on an edge device.

The shared [HTMX module](../modules/htmx/) vendors HTMX and its SSE extension,
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
   telemetry store. Aquarium and Keeper ask Mesh for data and render their own
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

Telemetry remains optional and belongs to Mesh. Mesh exposes a data-only feed at
`/mesh/api/projects/{project}/telemetry/stream`. It emits `telemetry` events whose
data is JSON:

```json
{"project":"default","node":1,"field":"temperature","value":"24.5","status":0}
```

The feed carries changes only; a reader asks `/telemetry/latest` for the current
state first. Applications still render their own templates from that data. The
gateway stays the single place that reaches drivers and devices.

## Verifying a change

- A request with `HX-Request: true` returns a fragment; a normal request still
  redirects or returns the page.
- `curl -N` on the event endpoint returns named events and a snapshot before
  live changes.
- The page holds one SSE connection, not one per component.
- Forms continue to work with JavaScript disabled.
