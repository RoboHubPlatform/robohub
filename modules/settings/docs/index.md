# Settings store

The parent application owns runtime settings; a module reads and writes a
namespaced key rather than a file beside itself.

```rho
let currency: string = settings_get("inventory.currency", "RON")
settings_set("inventory.currency", "EUR")
```

The file is `$ROBOHUB_APP_WORKSPACE/data/settings.conf`, one `key=value` per
line. A module without a host workspace falls back to `~/.rho/robohub`. Values
are plain text; a value containing an equals sign keeps it after the first one.

Configuration that belongs to a build or deployment — ports, routes, commands,
database drivers — stays in `module.yml`. This store is for values a user may
change at runtime.
