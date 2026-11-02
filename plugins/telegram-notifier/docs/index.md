# telegram-notifier

Posts an alert to a Telegram chat through the bot API.

## Settings

| Key | Meaning |
|-----|---------|
| `bot_token` | bot token from BotFather |
| `chat_id` | destination chat |
| `severity_threshold` | lowest level it accepts; default `WARNING` |

It is a webhook-shaped channel: the provider knows the API and the channel only
composes the text.
