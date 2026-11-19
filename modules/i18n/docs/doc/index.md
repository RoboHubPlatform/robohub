# Internationalisation

The module keeps a Rho page in the language the request asked for. Catalogs are
flat JSON files embedded by the host at build time; this module never parses a
file and never calls a network service.

## How an application uses it

Add `i18n` to `deps` and include it. It needs no host hooks; it registers
`POST /i18n/locale` on the application's router. Every shared module whose pages
are translated (`appshell`, `inventory`, `scheduler`, `rules`, `widgets`,
`journal`) depends on it.

## Catalogs

A catalog is a flat JSON file per language. A module ships its own in its
`module.yml`:

```yaml
locales:
  - locale: en
    file: locales/en.json
  - locale: ro
    file: locales/ro.json
```

and the application lists its own in its target in `project.yml`, with the
language a request gets when it names none:

```yaml
targets:
  - id: go-server
    default_locale: en
    locales:
      - locale: en
        file: locales/en.json
      - locale: ro
        file: locales/ro.json
```

The build embeds every catalog: the included modules' first, the application's
last. A later catalog overrides an earlier one, so an application can say a module's
word its own way. A file is a flat object of string values:

```json
{
  "dashboard.title": "System Status",
  "dashboard.temp": "Temperature: {{val}}°C"
}
```

## Templates

```html
<h1>{{t "dashboard.title"}}</h1>
<p>{{t "dashboard.temp" val=current_temp}}</p>
```

`{{val}}` in the catalog is replaced with the current template value and
escaped. A missing key falls back to the default language, then prints the key.

The active language is the reserved `__locale` value. `i18n_vars(req)` adds it,
and the switcher, to a page fill:

```rho
let body: string = template_fill(template_get("page"), vars("body", body) + i18n_vars(req))
```

## Choosing a language

1. the `locale` cookie, if it names a supported catalog;
2. the first supported `Accept-Language` tag;
3. `en`.

The supported languages are `en` and `ro`; a regional tag falls back to its
primary language (`ro-RO` is `ro`). `i18n_switcher(req)` draws the language
buttons (the `locale_switch` value `i18n_vars` adds), and the person's menu in
the top bar offers the same choice (see {ref}`ui/index`). Either posts to
`/i18n/locale`, which sets the `locale` cookie for a year and redirects to the
`next` path — only a path on this origin (`i18n_safe_next`). It also sends `HX-Redirect`, so an HTMX form works without a special client
path.

## Outside a template

`i18n_t(req, key)` translates a key for a notice or an error, and
`i18n_locale(req)` is the language a request is answered in.

An application that writes its labels in English can carry a catalog of whole
labels instead: `phrases.<locale>.txt` in a folder of its own, English and the
translation separated by a tab, one per line. `i18n_phrases(req, html, folder)`
turns a page into the request's language, replacing a label only where it is a
whole text between tags, a placeholder or a title; a whole page also carries the
catalog, so what arrives later (htmx, a live stream) is translated in the
browser.

## Coverage

The build compares each non-default catalog with the default one and prints
the number of missing keys, with the first key, plus any key the locale has that
the default does not. Missing keys fall back to the default language; the
warning is a prompt to finish the translation, not a build failure.

Live fragments carry the language in their event name, for example
`widget-1-en` and `widget-1-ro`, because one SSE connection serves clients that
may have chosen different languages.
