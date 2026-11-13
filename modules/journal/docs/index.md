# Journal

What happened in an installation, in one table: when, how serious, what kind of
thing, about what, who or what did it, and what was said. Every RoboHub
application that includes the module records in the same shape, so a page, a
badge or another application reads them the same way.

## Writing

```rho
journal_info("switch", "heater", "rule:keep-temperature", "switched off at 25.6 °C")
journal_warning("test", "aquarium", "person:ana", "NO₃ 28 mg/L, above the 25 target")
journal_error("device", "filter-main", "rule:filter-stopped", "the filter draws no power")
```

`journal_write(level, kind, subject, actor, message)` is the general form; the
level is `info`, `warning` or `error`. A warning or an error is also passed to
the notifications module, so a person sees it now and can read it later.

| Field | What it is |
|---|---|
| `kind` | what sort of thing: `switch`, `rule`, `mode`, `test`, `stock`, `system` |
| `subject` | what it was about: an inventory item's handle, a rule's name |
| `actor` | who or what did it: `person:<name>`, `rule:<name>`, `device`, `system` |

## Open entries

A warning or an error stays open until it is resolved, on the page or with
`journal_resolve(id)`. `journal_open_count()` is what a badge shows.
`journal_last_at(kind, subject)` is when the newest entry of a kind was written
("how long since the last water change"). `journal_prune()` drops what is older than three months and needs nothing more;
a host calls it from its background work.

## Reading

`GET /journal` is the page, filtered by level, kind and period.
`GET /api/journal?since=<unix>&level=&kind=` is the same as JSON:

```json
{"entries":[{"id":1,"at":1794578163,"level":"warning","kind":"test",
  "subject":"aquarium","actor":"person:ana","message":"NO₃ 28 mg/L","resolved_at":0}]}
```

## Storage

The table is the module's own (`db/schema.sql`, declared in its `sql:` block), in
the database of the application that includes it.
