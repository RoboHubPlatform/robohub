# Changelog

All notable changes to the gateway contract are recorded here, one section per release.

## [0.2.0] - 2026-11-12

The sim provider is retired. No application could reach it: energy's
simulation reaches widgets through Mesh, which serves every reading, and the
simulated endpoints the provider called were never served. The contract now
compiles in the mesh provider only.
