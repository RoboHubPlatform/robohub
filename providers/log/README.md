# robohub-provider-log

The `alert` contract's `log` transport.

```rho
include "../../providers/log/src/provider.rho"
provider_log_append("path=~/.rho/alerts.log", "WARNING: tank hot")
```

`path` is expanded from `~`. The provider creates the parent directory and
returns `1` when the line was written.
