# Changelog

All notable changes to the gateway contract are recorded here, one section per release.

## [0.2.0] - 2026-11-12

The sim provider is retired. No application could reach it: energy's
simulation reaches widgets through Mesh, which serves every reading, and the
simulated endpoints the provider called were never served. The contract now
compiles in the mesh provider only.

## [0.2.1] - 2026-11-12

The contract declares `rho-log`, which the mesh provider it includes imports, and calls the language's string functions.

## [1.0.0] - 2026-11-12

The gateway contract is the gateway interface, `robohub-gateway` (import
`robohub.gateway`), and its manager is gone. An application declares the
interface and the provider it uses, binds the provider in its `module.yml` with
Mesh's address and the project, and calls `gateway.sources()`,
`gateway.source_latest(...)` and the rest; the first enabled provider bound
answers. `gateway.config` and `gateway.configure` read and change the
provider's settings on a running installation. The `plugins:` block and the
`gateway.conf` file are no longer read, and the `mesh-gateway` plugin is
removed.
