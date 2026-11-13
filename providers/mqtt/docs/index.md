# robohub-provider-mqtt

The MQTT provider of the bus interface (`robohub.bus`). It publishes at QoS 1
and follows a filter in the background, keeping the newest message per topic,
through the RoboHub platform's `mqtt` port: a program that binds this provider
gets the port.

```yaml
bind:
  robohub.bus:
    providers: [robohub-provider-mqtt]
    config:
      robohub-provider-mqtt:
        broker: "mqtt://127.0.0.1:1884"   # optional
```

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `broker` | `ROBOHUB_BUS_URL` | the broker's URL |
| `user` | `ROBOHUB_BUS_USER` | the broker user |
| `password_file` | `ROBOHUB_BUS_PASSWORD_FILE` | the file the password is in |

The defaults are what the keeper starts the application with: it runs the broker
(the `robohub-mqtt` plugin) and makes a broker user for every application that
binds the bus, allowed the topics its manifest's `bus:` block names. The
password is read from its file by the port and never passes through a setting or
a command line.
