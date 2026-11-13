# RoboHub UI

The look every RoboHub application shares: one stylesheet, one top bar, one
theme choice.

## Using it

```yaml
deps:
  robohub:
    ui: ">=0.1.0"
```

```rho
include "ui"
```

The module serves `/ui/robohub.css` and `/ui/robohub.js`. A page puts
`ui_head()` in its `<head>`, `ui_theme(req)` in the `data-theme` attribute of its
`<html>`, `class="rh"` on its `<body>`, and draws the top bar:

```rho
let person: string = ui_person(req, "Ana", "operator", "", "/logout")
let bar: string = ui_topbar("mesh", apps, "", person)
```

`apps` is one application per line, `name|title|port|route|state`, with an empty
port for the application drawing the page. The switcher opens another
application at its own port on the host the page was reached on.

## Themes

Dark is the default. `/ui/theme?set=light|dark|system&back=<path>` keeps the
choice in the `rh_theme` cookie; a cookie belongs to the host rather than the
port, so every application on the machine opens in the same theme. Every colour
in the stylesheet is a token, and the light theme redefines the tokens only.

## Components

| Class | What it is |
| --- | --- |
| `rh-top`, `rh-rail`, `rh-main`, `rh-strip` | the shell: top bar, left rail of places, page, bottom strip |
| `rh-split`, `rh-canvas`, `rh-ins` | a canvas with an inspector beside it |
| `rh-grid`, `rh-card` (`svc`, `int`, `keeper`, `sel`, `needs`) | a grid of things |
| `rh-pill` (`ok`, `warn`, `bad`, `busy`) | the one state a card shows |
| `rh-chips`, `rh-chip` | filters |
| `rh-ins-h`, `rh-kick`, `rh-tabs`, `rh-body`, `rh-row`, `rh-impact`, `rh-foot` | the inspector's parts |
| `button`, `.quiet`, `.danger`, `.notice`, `.grid`, tables | plain elements |
