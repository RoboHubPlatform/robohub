# Settings store

The values a person may change while an application runs, kept in the
application's own workspace. A module reads and writes a namespaced key rather
than a file beside itself, so every module an application includes shares one
store and two applications never share one.

## How an application uses it

Add `settings` to `deps` and include it. It needs no host hooks and serves no
routes; the modules that have settings (`logging`, `inventory`, `scheduler`,
`widgets`) call it themselves, and their settings forms are shown on the
application's settings page (see {ref}`appshell/index`).

```rho
let currency: string = settings_get("inventory.currency", "RON")
settings_set("inventory.currency", "EUR")
let mine: string = settings_list("inventory.")   // `key=value` lines
```

- `settings_get(key, fallback)` — the stored value, or `fallback` when the key
  is not there.
- `settings_set(key, value)` — stores a value, replacing the key's line or
  adding one.
- `settings_list(prefix)` — every `key=value` line whose key starts with
  `prefix`, so a host can draw a generic editor for a module that has no form of
  its own.

## Where it is kept

`<workspace>/data/settings.conf`, one `key=value` per line. The workspace is the
one the supervisor gives the application (`RHO_APP_WORKSPACE`, or
`ROBOHUB_APP_WORKSPACE`); a program started by hand uses
`~/.rho/apps/<app>`. Values are plain text, and a value containing an equals
sign keeps it after the first one.

Each module keeps its keys under its own prefix: `log.*`, `inventory.*`,
`scheduler.*`, `widgets.*`. The keys each module reads are listed on its own
page.

Configuration that belongs to a build or deployment — ports, routes, commands,
database drivers — stays in `module.yml`. A provider's settings are not kept
here either: they are its `bind:` values, overridden by the application's
`bind.conf`. This store is for values a person may change at runtime.
