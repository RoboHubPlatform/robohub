# mesh-gateway

The RoboHub Mesh gateway, as a provider behind the gateway contract.

An application asks the contract for a project list, a gateway address, the
sources of a project, device states, or the state behind one source URL. It
never names `/mesh/api`; this provider does. A different mesh is another plugin
with the same `plugin.kind: gateway` and its own transport, and an application
switches by naming that plugin in its `plugins:` block.

```yaml
plugins:
  - name: mesh-gateway
    enabled: true
    config:
      url: http://127.0.0.1:8478
      project: default
```

The settings an application exposes can override the config by writing
`gateway.conf` beside its database; the manager merges it over the manifest's
values.

## Telemetry

`gateway_source_latest(source)`, `gateway_source_history(source, from_ms,
to_ms, step_ms)` and `gateway_telemetry_status()` are the telemetry half of the
same contract. The source may be the ID from `gateway_sources`, a value or
action URL, or a URL carrying `source=`; all three name the same series.

`gateway_source_history` with empty `from` and `to` means the last 24 hours, and
an empty `step` means raw readings. A step is in milliseconds; a chart that
wants a day at a readable resolution asks for `900000`.

Aquarium's existing widgets already store Mesh value URLs; they resolve to the
same series through this provider, so a chart began using Mesh history without a
stored-source migration.
