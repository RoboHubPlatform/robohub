# robohub-bus

The message bus interface. An application publishes to a topic, follows a topic
filter and reads the newest message of a topic, through the broker provider it
binds. A bus is one broker, so the first enabled provider bound is the one used.
The provider today is `robohub-provider-mqtt`, on the broker the `robohub-mqtt`
plugin runs.

```yaml
deps:
  robohub-bus: ">=0.2.0"
  robohub-provider-mqtt: ">=0.2.0"
bind:
  robohub.bus:
    providers: [robohub-provider-mqtt]
```

With no settings the provider uses the broker the keeper gave the application
(`ROBOHUB_BUS_URL`, `ROBOHUB_BUS_USER`, `ROBOHUB_BUS_PASSWORD_FILE`).

## What an application calls

| Function | What it does |
|---|---|
| `publish(topic, payload, retain)` | sends a message; `retain` keeps it as the topic's last word for later subscribers; answers whether the broker took it |
| `follow(filter, events_path)` | follows a filter (`shelly/+/status/#`) in the background; each message becomes its topic's newest, and a JSON line in `events_path` when set |
| `follow_lines(filter, lines_path)` | appends every payload to a file as it came, one per line: the other end of `relay` |
| `relay(lines_path, topic)` | publishes every line appended to a file from now on: a file carried across the broker unchanged |
| `latest(topic)` | the newest message heard on a topic, or `""` |
| `topics(prefix)` | the topics heard under a prefix, newest first: topic, seconds since, payload, tab-separated |
| `provider()`, `config(key)` | the provider that answers, and one of its settings |

## What a provider implements

`publish`, `follow`, `follow_lines`, `relay`, `latest` and `topics`, with the
signatures in `interface: functions:` of `module.yml`.
