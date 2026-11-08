# Internationalisation

The module keeps a Rho page in the language the request asked for. Catalogs are
flat JSON files embedded by the host at build time; this module never parses a
file and never calls a network service.

## Catalogs

The host lists its files in `project.yml`:

```yaml
default_locale: en
locales:
  - locale: en
    file: locales/en.json
  - locale: ro
    file: locales/ro.json
  - locale: en
    file: ../../../modules/i18n/locales/en.json
  - locale: ro
    file: ../../../modules/i18n/locales/ro.json
```

Later files override earlier ones, so an application can replace a module
string. A file is a flat object of string values:

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

The layout shows two flag buttons, one per supported language. Clicking one
posts to `/i18n/locale`, which sets the cookie and redirects to the local `next`
path. It also sends `HX-Redirect`, so an HTMX form works without a special client
path.

## Coverage

`rho build` compares each non-default catalog with the default one and prints
the number of missing keys, with the first key, plus any key the locale has that
the default does not. Missing keys fall back to the default language; the
warning is a prompt to finish the translation, not a build failure.

Live fragments carry the language in their event name, for example
`widget-1-en` and `widget-1-ro`, because one SSE connection serves clients that
may have chosen different languages.
