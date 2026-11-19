# HTMX

A pinned copy of [HTMX](https://htmx.org) and its
[SSE extension](https://github.com/bigskysoftware/htmx-extensions), vendored so
an off-grid RoboHub deployment never reaches for a CDN and no application needs
Node, npm or a bundler.

| File | Version | License |
| --- | --- | --- |
| `assets/htmx.min.js` | 2.0.11 | 0BSD (`assets/LICENSE-htmx`) |
| `assets/sse.min.js` | 2.2.4 | 0BSD (`assets/LICENSE-sse`) |

The npm package integrity values recorded when the files were taken were
`sha512-Thx/WtpeOQqSrqBCw/A1cwGJGg4UrVa3+sW0GmrM3p4gJgO89ecH4qtbnyzDDWFvBTqjnIMCgELTNt636dtamA==`
for `htmx.org@2.0.11` and
`sha512-LJmxVhykyflBWgh5PvbRidcyuqMHlgfajmmzumvKctv9puvsufeH6OaejSMZTNTnEI8O2wXXn4ZZtBdpEMqmEQ==`
for `htmx-ext-sse@2.2.4`.

## Using it

Add the module to `deps` and include it by name, then put `htmx_head()` in the
page layout. It needs no host hooks and has no settings.

```yaml
deps:
  robohub:
    htmx: ">=0.1.0"
```

```rho
include "htmx"
```

```html
<head>
  {{{ htmx_head() }}}
</head>
```

The module registers `GET /assets/{file}` and serves only the two files above.

## Answering a request

A handler answers a fragment when HTMX made the request and the full page when
a browser made it:

```rho
fn widget_toggle(req: Request) Response {
    let card: string = ... // the rendered component
    if htmx_is_request(req) {
        return html(status_ok(), card)
    }
    return redirect("/widgets")
}
```

Form submissions keep their normal POST behaviour when JavaScript is off; HTMX
only changes what the successful response is.

## Live updates

The host opens one SSE connection per page and names each event. `sse_events`
streams JSON lines as named events with HTML data:

```html
<div hx-ext="sse" sse-connect="/events">
  <div id="temperature" sse-swap="temperature"></div>
</div>
```

The host writes `{"event":"temperature","data":"<div ...>"}` lines to its event
file. The snapshot file is sent first, so a page that connects sees current
state before later changes.

## Helpers

- `htmx_head()` — the two script tags.
- `htmx_is_request(req)` — whether `HX-Request` is true.
- `htmx_redirect(location)` — a redirect HTMX follows as a page change.
- `htmx_trigger(resp, event)` — dispatch a client event after a swap.
