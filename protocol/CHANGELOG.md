# Changelog

## [1.0.0] - 2026-11-14

The wire protocol has one source: the schemas the gateway carried — `common`,
`link`, `uplink` and `gateway`, namespace `robohub.v1` — moved here, with
`consumers.yml` naming the eight places they are generated from and
`tools/sync.py` writing every copy and regenerating its code. The two
robohub-devices nodes had fallen behind: their copies lacked `SensorReading`
and their generated code lacked the `PLUG` device kind; both are the source's
now.

## [1.1.0] - 2026-11-14

`RELAYED` (19): a relay carries a board's handshake and sealed frames unchanged inside its own sealed frame, so the gateway checks the board itself and a relay can only drop or delay.
