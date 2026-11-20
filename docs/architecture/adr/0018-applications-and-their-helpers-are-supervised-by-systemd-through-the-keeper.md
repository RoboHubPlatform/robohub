---
id: ADR-0018
title: Applications and their helpers are supervised by systemd through the keeper
status: accepted
date: 2026-11-20
requirements: [SYS-0070, SYS-0039, SYS-0004]
supersedes: []
superseded_by: []
---

# Applications and their helpers are supervised by systemd through the keeper

## Context

The keeper turns each application into a systemd user unit it writes
(`Type=simple`, `Restart=on-failure`, `RestartSec=5`, `NoNewPrivileges`, run from
a release through a `current` link), probes `/healthz` only after a redeploy, and
leaves systemd's defaults for everything else (`KillMode=control-group`, a start
limit of 5 in 10 s, a 90 s stop timeout). A Rho application is one Go binary:
the generated server serves every connection concurrently on every core, stops
on SIGTERM with a 30 s grace, and has header, idle, header-size and body-size
limits.

The question was whether a Gunicorn-like layer (a master that forks and
recycles workers) would make the applications more robust. It would not: that
model exists for interpreters that serve one request per process; a Go server
already does what the workers are for, and systemd is what such a master runs
under anyway. What was found instead, on this installation (systemd 249, WSL2,
cgroup v1, no user D-Bus session):

1. **A restart waits 30 s.** `http.Server.Shutdown` waits for open requests,
   and a page's live-update stream (SSE) never ends by itself, so every restart
   with a page open waits out the grace period.
2. **A hung application is never restarted.** systemd restarts a process that
   exits, not one that is alive and stuck; the keeper's probe runs only during a
   redeploy.
3. **The restart policy gives up.** `on-failure` leaves an application down
   when it exits 0 unexpectedly, and five quick failures stop the restarts for
   good.
4. **Helpers die with their application.** Mesh starts the native gateway and a
   coordinator's Zigbee2MQTT with `nohup`, so they live in `mesh.service`'s
   cgroup: every Mesh redeploy kills both, and their crashes are seen only by
   Mesh's own retry. Mesh cannot make them units of their own: `systemd-run
   --user` needs a user D-Bus session, which this machine does not have.
5. **No resource limits.** One leaking application can starve the machine; and
   on cgroup v1 a user unit's limits are not enforced at all.
6. **The keeper's isolation is off here.** The keeper asks `systemd-run --user`
   whether it can give an application a private view of the file system; the
   call fails for want of D-Bus, so the keeper concluded it cannot, and every
   application runs able to read the keeper's signing key and tokens (KEEP-0006
   unmet).

## Decision

Decided by the maintainer on 2026-11-20 (Phase 1 of the analysis):

1. **systemd stays the supervisor; no application-server layer is added**, and
   no socket activation for now (D1): with streams ending at shutdown a restart
   takes about a second, which is enough for the traffic expected.
2. **The generated server ends its streams at shutdown.** The requests' base
   context is cancelled as shutdown begins, so a stream returns at once and the
   grace period only covers real work (rho).
3. **The generated server tells systemd it is ready and alive.** When systemd
   gives it a notify socket it says `READY=1` once it listens, and, when systemd
   asks for a watchdog, `WATCHDOG=1` every half period only while a request to
   its own `/healthz` answers; a server that cannot answer itself is restarted.
   The binary carries the marker `rho-sd-notify-v1`, so the keeper knows it can
   ask for this (rho).
4. **The keeper's units restart always and forever**: `Restart=always`,
   `RestartSec=5`, `StartLimitIntervalSec=0`, `TimeoutStopSec=20` (a process
   that ignores SIGTERM is killed), and — for a binary with the marker —
   `Type=notify`, `NotifyAccess=main`, `WatchdogSec=30` (keeper).
5. **Resource limits are declared** in an application's manifest
   (`deploy.limits: {memory, tasks, cpu_weight}`) with defaults (2 GB, 1024
   tasks, weight 100) written as `MemoryMax`, `TasksMax` and `CPUWeight`; the
   keeper says on the application's page when the machine cannot enforce them
   (no cgroup v2 delegation), rather than pretend (keeper).
6. **Helpers are units the keeper writes and runs (D2)**, asked for by the
   application over the keeper's API: an application declares the helper names
   it may run (`helpers: [z2m-*, gateway-*]`); `POST /api/v1/helpers` on
   loopback, authenticated by the application's own client secret, writes
   `rh-<app>-<name>.service` (the program and its arguments, working directory,
   environment without secrets, a log file in the application's workspace, the
   same restart policy, `NoNewPrivileges`), enables and starts it; the keeper
   lists an application's helpers with their state, stops or restarts them on
   request, and removes them with the application. Helpers outlive a restart of
   their application. The keeper uses `systemctl --user`, which needs no D-Bus.
7. **Mesh runs its native gateway and each native coordinator's Zigbee2MQTT as
   helpers** when the keeper runs it, and as processes as today when it runs on
   its own (a developer's machine, CI) (mesh).
8. **The keeper's isolation probe runs a throwaway unit through `systemctl
   --user`**, not `systemd-run`, so a machine without a user D-Bus session gets
   the isolation its systemd can give (keeper). The isolation an application's unit gets includes
   `PrivateUsers=yes`: a user manager can only make the private mount view inside
   a user namespace (without it, systemd 249 on WSL refused with 226/NAMESPACE);
   supplementary groups such as `dialout` still grant access, unmapped.

## Consequences

- A redeploy is seconds, not half a minute; a hung application is restarted
  within about 30 s; nothing stays down because it failed five times.
- A Mesh redeploy no longer drops the Zigbee network or the gateway; helpers are
  started at boot by systemd itself, so they no longer wait for Mesh — or for
  the keeper — to come up.
- With isolation working, applications lose read access to the keeper's folder
  except their own workspace and releases; an application that read something
  of the keeper's directly will now fail and is fixed to use the keeper's API.
- Limits do nothing on this machine until WSL runs cgroup v2 (or RoboHub moves
  to a Linux host); the keeper says so.
- An application built with an older rho has no marker and gets no watchdog,
  only the restart policy.

## Alternatives considered

- **A Gunicorn-like master in rho** (pre-fork, rolling restarts) — duplicates
  what Go's server and systemd already do; its one gain, keeping the port open
  across a restart, is socket activation, deferred.
- **Socket activation now** — no refused connections during the second a
  restart takes; not needed at this traffic. Deferred, not rejected.
- **Transient units created by the application (`systemd-run --user`)** — no
  keeper API, but it needs a user D-Bus session this machine does not have, and
  the keeper would not know the units. Rejected.
- **Installing `dbus-user-session`** — would make `systemd-run --user` work, but
  needs root and a WSL restart, and the keeper would still have to work where it
  is missing. Not relied on.
- **Containers (Docker or Podman) with restart policies and health checks** —
  robust, but a second runtime to keep, and USB devices into a container under
  WSL are awkward. Rejected for the native host.
