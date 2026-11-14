# RoboHub UI

The look every RoboHub application shares: one stylesheet, one top bar with the
application switcher and the person's menu, one theme choice and the bar's words
in English and Romanian. The keeper, Mesh, aquarium and energy all draw their
pages with it.

## Using it

```yaml
deps:
  robohub:
    ui: ">=0.1.0"
```

```rho
include "ui"
```

The module needs no host hooks. It serves `/ui/robohub.css`, `/ui/robohub.js`
and `/ui/theme` on the application's router. A page puts `ui_head()` in its
`<head>`, `ui_theme(req)` in the `data-theme` attribute of its `<html>` and
`class="rh"` on its `<body>`, then draws the top bar.

## The top bar

The bar is the brand, the application switcher, what the application adds in
the middle (HTML), and the person's menu.

```rho
let person: string = ui_person(req, "Ana Example", "operator",
    ui_language(locale, request_path(req)), signout, true)
```

`ui_person(req, who, role, links, signout, themes)` is the person's menu: their
initials and name, the role when one is given, the theme choice when `themes`
is true, the links the application adds (HTML; `ui_language` is the language
choice, posted to the `i18n` module's `/i18n/locale`) and `signout` last.

There are two ways to draw the switcher:

- **`ui_topbar_in(current, apps, middle, person, locale)`** — the application
  knows the list. `apps` is one application per line,
  `name|title|port|route|state`. An empty port is this application, opened at
  `route` on this host; a port opens the application at that port on the host
  the page was reached on. The one named `current` is marked. The keeper draws
  its bar this way.
- **`ui_topbar_remote_in(current, title, keeper_port, middle, person, locale)`**
  — an application that is not the keeper. The bar names the application, and
  the page's script fills the list from the keeper's `/api/v1/switcher` on
  `keeper_port` of the same host (the answer carries no credential). An
  application the keeper serves behind its own origin (a `path` in that answer,
  such as `/app/aquarium/`) is linked through the keeper, so its own port is never
  visited; otherwise it is linked at its port. Until the keeper answers, the list
  holds the way back to the keeper. Applications that include `appshell` get
  this bar from `appshell_topbar`.

`ui_topbar` is `ui_topbar_in` in the default language.

## State words

A state in the switcher is shown with a coloured dot and a word.
`ui_state_word(locale, state)` is the word for a state in a language, and a state
it has no word for is shown as it is.

| State | Dot | English | Romanian |
|---|---|---|---|
| `running`, `keeper` | ok | running, keeper | pornită, keeper |
| `starting`, `not-built` | warn | starting, not built | pornește, neconstruită |
| `failed` | bad | failed | eșuată |
| `stopped` and anything else | off | stopped | oprită |

## Locales

The bar's own words (`ui.applications`, `ui.theme.*`, `ui.language`,
`ui.state.*`, `ui.keeper`) are in `locales/en.json` and `locales/ro.json`, which
travel with the module, so any application that includes it has them. The
language is the request's `locale` cookie (`en` or `ro`), set by the `i18n`
module; with none, the default language is used.

## Themes

Dark is the default. `/ui/theme?set=light|dark|system&back=<path>` keeps the
choice in the `rh_theme` cookie and returns to `back` (only a path on this host).
A cookie belongs to the host rather than the port, so every application on the
machine opens in the same theme. Every colour in the stylesheet is a token, and
the light theme redefines the tokens only.

## What the script does

`/ui/robohub.js` fills the links to other applications, shows times
(`.local-time[data-ms]`) in the reader's zone, closes an open menu when the
reader clicks elsewhere, and marks the card whose inspector is open. It runs
again after every htmx swap.

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
