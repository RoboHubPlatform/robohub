# Notifications

Short messages a person sees on the page they have open — "Saved.", "The widget
could not be added" — shown as a toast, kept for a few seconds and then gone. A
change made anywhere in the application reaches every open page of it without a
refresh, because each page follows the same live feed.

This is the application's own toast, for the person using it. Alerts that leave
the application (email, Telegram, a webhook) go through the `robohub.alert`
interface and its providers instead (see {ref}`robohub-alert/index`).

## How an application uses it

Add `notifications` to `deps` and include it. It needs no host hooks; its
routes are registered on the application's router.

- Put `notification_embed()` in the page body of the application's layout. It
  draws the toast and opens an `EventSource` on `/notifications/stream`. Each
  event is shown as a toast and also dispatched on the window as a `rho:event`
  (its `detail` is the event), so a page that cares about a change can reload
  its own data without knowing where the change came from. An event for another
  language than the page's (`<html lang>`) is not shown.
- Push a message from a handler:

```rho
notification_push_level_locale(i18n_t(req, "toast.widget_added"), "info", 10, i18n_locale(req))
notification_push_level("Backup finished", "info", 0)   // 0 = the default 5 seconds
notification_live_event("refresh", "inventory changed")  // live only, not kept
```

`notification_push_level_locale(message, level, timeout, locale)` stores the
message with the time it expires (`timeout` seconds from now) and appends it to
the live feed; `notification_push_level` is the same for every language. The
level is `info`, `warning` or `error`. `notification_live_event(kind, message)`
appends an event to the live feed only, so it is a page-to-page message rather
than a stored notification.

`widgets`, `inventory`, `scheduler`, `journal` and the applications use it for
their toasts.

## Routes

| Route | What it does |
|---|---|
| `POST /notifications/push` | Pushes a message (`message`, optional `level` and `timeout`) |
| `GET /notifications/list`, `GET /api/notifications` | The active messages, newest first, as JSON |
| `POST /notifications/dismiss` | Dismisses one message (`id`) |
| `GET /notifications/render` | The active messages as HTML |
| `GET /notifications/stream` | The live feed, as Server-Sent Events |

## Data it keeps

In the application's workspace (`<workspace>/data`):

| What | Where | What it holds |
|---|---|---|
| `notifications` table | `app.db` (or `RHO_NOTIFICATIONS_DB`) | Each message: level, text, when it was created, when it expires, whether it was dismissed |
| The live feed | `live.events` | One JSON event per line (`kind`, `message`, `locale`), streamed to open pages |

The module has no settings.
