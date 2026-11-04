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
