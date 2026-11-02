# webhook-alert

Posts an alert to an HTTP endpoint as a small form body:
`level`, `message` and `metadata`.

## Settings

| Key | Meaning |
|-----|---------|
| `url` | endpoint that receives the POST |
| `content_type` | defaults to `application/x-www-form-urlencoded` |
| `authorization` | optional `Authorization` header |
| `severity_threshold` | lowest level it accepts |

A service that needs a signed body or a richer JSON document is the next
provider, not a change to the alert rule.
