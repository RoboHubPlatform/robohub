# Plugins

Every directory in this folder is an installed plugin: it has a `module.yml`
with an identity, a `src/main.rho`, documentation, and a changelog, and it is
listed in `registry.yml`. A directory without those is not a plugin and does not
belong here.

The plugins are `robohub-auth`, how an application signs a person in, and
`mesh-gateway`, the gateway contract's mesh implementation.

Alert channels are not plugins. They are providers of the alert interface
(`contracts/alert/`, `robohub-alert`): an application depends on the providers
it wants and binds them in its `module.yml`. See `providers/README.md`.

## Dependencies

Every module a host imports or includes, every module in its `modules:` block,
and every plugin in its `plugins:` block is declared under `deps.robohub` in that
host's `module.yml`:

```yaml
deps:
  rho-log: ">=0.1.0"     # a Rho component
  robohub:
    forms: ">=0.1.0"     # a RoboHub module, interface, provider or plugin
    robohub-auth: ">=0.1.0"
```

The version lives in `deps.robohub` only. A `modules:` entry carries where the
module sits and how the host configures it; the `plugins:` entry carries its
settings. Repeating the version in those blocks is refused. `rho build` refuses
an import or include whose module is not declared under `deps.robohub`, and
`scripts/check-deps.py` checks the same rule for every manifest in the tree.
