# robohub-provider-telegram

The `alert` contract's `telegram` transport.

```rho
include "../../providers/telegram/src/provider.rho"
provider_telegram_send("bot_token=...;chat_id=...", "Tank above 28 C")
```

Both `bot_token` and `chat_id` are required; the provider returns `1` when the
Bot API accepted the message.
