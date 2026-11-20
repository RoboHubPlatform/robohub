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

## [1.2.0] - 2026-11-14

`REKEY` (20) and `REKEY_ACK` (21): a gateway hands a board its next key sealed under the current one, and the board confirms with a proof made under the new key.

## [1.3.0] - 2026-11-14

`SESSION_RESET` (22): a gateway that restarted asks a board, sealed under the session it restored, to start a new session.

## [1.4.0] - 2026-11-20

`HEALTH` (0x0403, PROTO-0007, robohub ADR-0021): a board's account of its last restart — the reset reason (`ResetReason`, robohub-common's set), the boot count, the last fault record (code, task, program counter, uptime) and the firmware version — sent once per boot after its session is up and again on a `DIAG_REQUEST`; a receiver that does not know it drops it. `consumers.yml` names the device-node runtime at its new place, `robohub-node/device-node`.
