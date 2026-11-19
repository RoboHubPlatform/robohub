# Plugins

Every directory in this folder is a plugin: it has a `module.yml` with an
identity, documentation and a changelog. A plugin the keeper manages is listed in
`registry.yml`, which is what the keeper lists and what its install and
uninstall actions edit. A plugin another application reads as data — today
`robohub-zigbee2mqtt`, which Mesh reads — is not in `registry.yml`, where the
keeper would offer to enable or disable something it does not use; it has an
entry in `registry/modules/` (`role: plugin`) instead, which is how Mesh finds
it. A directory without a manifest, docs and a changelog is not a plugin and does
not belong here.

| Plugin | What it is |
|---|---|
| `robohub-auth` | How an application signs a person in, with the keeper as the authorization server. Its middleware is generated from the application's `project.yml` (see {ref}`robohub-auth/index`) |
| `robohub-mqtt` | An integration plugin with no code of its own: a Mosquitto broker the keeper runs as a user service on port 1884, with a broker user for every application that binds `robohub.bus` and for each device an admin adds. Applications reach it through `robohub-provider-mqtt` (see {ref}`robohub-mqtt/index`) |
| `robohub-zigbee2mqtt` | A data-only plugin Mesh reads, not the keeper: Zigbee2MQTT pinned at 2.14.3 (source and container image), the Node.js it needs (`system_deps`), and the configuration template Mesh writes for each Zigbee coordinator (see {ref}`robohub-zigbee2mqtt/index`) |

Alert channels, the Mesh gateway and the MQTT client are not plugins. They are
providers of an interface (`contracts/alert/`, `contracts/gateway/`,
`contracts/bus/`): an application depends on the providers it wants and binds
them in its `module.yml`. See `providers/README.md`.

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
