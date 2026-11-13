# Application API

What an application offers other applications, the keeper and external clients:
a small read-only REST API, the same in every RoboHub application. It is not a
gateway — it has no projects, devices or actions — but it serves more than the
application received from its gateway: the values it derives, the values it
computes itself, and the readings it chooses to pass on, each with its history,
and its journal.

## Values

| Kind | Where it comes from |
|---|---|
| `derived` | the application's `presets/api.yml`, computed by `appapi_tick()` |
| `published` | the application's own code: `appapi_publish(id, value, unit, label)` |
| `export` | an inventory item's reading it passes on (`fn: export`) |

```yaml
# presets/api.yml
values:
  temperature_avg_24h:
    from: heater.temperature
    fn: avg
    window: 24h
    unit: °C
    label: Water temperature, 24 h average
  days_since_water_change:
    from: water_change
    fn: since
    unit: d
  heater_energy_month:
    from: heater.power
    fn: integral
    window: 30d
    unit: Wh
  heater_temperature:
    from: heater.temperature
    fn: export
    unit: °C
```

`from` is an inventory item's capability by handle, or for `since` a journal kind
(`kind` or `kind.subject`). `fn` is `latest`, `avg`, `min`, `max`, `integral` (over
time: watts become watt-hours), `since` (days since the newest journal entry of
that kind) or `export`. `appapi_presets(text)` reads the file; `appapi_value(id)`
is a value's newest text, which is what a host answers a rule with.

## Endpoints

| Path | Answers |
|---|---|
| `GET /api/v1/values` | `{"application":"aquarium","values":[{"id","value","unit","label","kind","updated_at"}]}` |
| `GET /api/v1/values/{id}` | one value |
| `GET /api/v1/values/{id}/history?from=&to=` | `{"ok":true,"points":[{"t":ms,"v":value}]}`, the gateway's own shape; the last day by default |
| `GET /api/v1/events?since=&level=&kind=` | the journal, as the journal module serves it |

The paths are read-only, so a keeper token with only the application's `:read`
grant reaches them. History is kept for 30 days.

## The host

The host includes the module after inventory and journal and calls
`appapi_tick()` from its background work, about once a minute.
