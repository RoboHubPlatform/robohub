# robohub-provider-telegram

An alert channel that posts each alert to a Telegram chat through a bot. It
implements the `robohub.alert` interface (its `send`), and the application calls
`alert.raise(...)`, never the provider (see {ref}`robohub-alert/index`).

## Binding it

```yaml
deps:
  robohub:
    robohub-alert: ">=1.1.0"
    robohub-provider-telegram: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-telegram]
    config:
      robohub-provider-telegram:
        severity_threshold: WARNING
```

Put `bot_token` and `chat_id` in the application's `bind.conf` (the settings
page writes them there) rather than in the manifest: the token is a secret.

## Settings

| Setting | Default | What it is |
|---|---|---|
| `bot_token` | — | The bot's token from BotFather; required |
| `chat_id` | — | The chat the bot posts to; required |
| `severity_threshold` | everything | The lowest level posted: `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `enabled` | on | `"false"` stops the channel |

The message is `[<level>] <message>`, with the metadata on a second line. The
token and the chat id must be what Telegram issues (letters, digits, `:`, `-`,
`_`); anything else is refused. The token is passed to `curl` through an
owner-only file, never on a command line. `send` answers `1` when the Bot API
accepted the message.
