# robohub-alert

The alert interface. An application raises an alert; every channel it binds
delivers it, unless the channel is disabled or the alert is below the channel's
severity threshold. The channels are providers: `robohub-provider-log`,
`-email`, `-telegram` and `-webhook`.

```yaml
deps:
  robohub:
    robohub-alert: ">=1.1.0"
    robohub-provider-telegram: ">=0.2.0"
    robohub-provider-log: ">=0.2.0"
bind:
  robohub.alert:
    providers: [robohub-provider-telegram, robohub-provider-log]
```

```rho
import robohub.alert

let delivered: u32 = alert.raise("WARNING", "Tank too warm", "{\"tank\":\"main\"}")
```

The interface only is a dependency of a shared module such as `rules`; the
application chooses the channels. An application that binds none raises alerts
that reach no channel (`raise` answers 0) — `rules` writes them to the journal
either way.

## Settings every channel has

Besides its own settings (listed on each provider's page), every channel
accepts two the interface reads:

| Setting | What it does |
|---|---|
| `enabled` | `"false"` stops the channel receiving alerts; anything else, or nothing, leaves it on |
| `severity_threshold` | The lowest level the channel receives: `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Empty receives everything |

Levels are compared by name, in capitals: `INFO` < `WARNING` < `ERROR` <
`CRITICAL`, and a level the interface does not know ranks with `INFO`.

A channel's settings are its `bind:` values, and the application's `bind.conf`
(`<provider>.<key>=value` lines in its workspace) wins over them, so
`configure(provider, key, value)` changes a setting on a running installation
without a rebuild.

## What an application calls

| Function | What it does |
|---|---|
| `raise(level, message, metadata)` | delivers an alert to every enabled channel it meets the threshold of; answers how many accepted it |
| `test(provider, message)` | sends through one channel whatever its settings, for a settings page to show the channel works |
| `providers()` | the channels the application binds, one per line |
| `enabled(provider)` | whether a channel receives alerts: unless its `enabled` setting says false |
| `config(provider, key)`, `configure(provider, key, value)` | one of a channel's settings, read or changed on the running installation |

## What a channel implements

```
send(level: string, message: string, metadata: string) u32
```

The calls to the channels are generated from the application's binding, so
neither the interface nor the application names a provider's internals.

## The alert state machine

`alert_rule_new(id, name, threshold, hysteresis, pending_seconds,
cooldown_seconds, max_per_window, window_seconds)` makes a rule, and
`alert_rule_evaluate(rule, value, now)` advances it by one sample, answering an
`AlertEvaluation`: the next rule, and whether it `fired` or `cleared`. A rule is
a value; the caller keeps the one it is given back.

- **normal → pending** when the value reaches the threshold;
- **pending → triggered** once it has stayed there `pending_seconds` (at once
  when that is 0), and back to normal if it does not;
- **triggered → cooldown** when it falls below the threshold less the
  hysteresis;
- **cooldown → normal or pending** after `cooldown_seconds`.

A rule fires at most `max_per_window` times in `window_seconds` (0: no limit).
Times are seconds from any monotonic source the application chooses.
