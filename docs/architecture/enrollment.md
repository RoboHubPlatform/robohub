# Enrolling a node

A gateway accepts readings only from a board it can authenticate, and the keeper
issues credentials only to a node that proved it holds a one-time token. There
are two kinds of identity, for two kinds of node.

| Node | Identity | Made by | Checked by |
|---|---|---|---|
| A board Mesh builds (Pico, ESP32, …) | a device key derived from its gateway's key and its id | Mesh, when it builds the image | the gateway, on every frame |
| A Linux host with a key of its own | an Ed25519 key pair and a credential the keeper issued | `rho bootstrap` on the node, the keeper's `/api/enroll` | the keeper's `/api/nodes/verify` |

## Boards: enrolled by being built

Nothing is typed in for a board; its identity is part of its build.

1. **The gateway key.** Each mesh's gateway has a 256-bit key, `K_gw`, made the
   first time it is needed and kept in the mesh's folder as `gateway.key`,
   readable by Mesh's user only. Mesh installs it beside the gateway it starts,
   pushes or deploys, and tells the gateway where it is (`GATEWAY_KEY_FILE`).
2. **The board's id.** Every planned board has a 64-bit id, `node.<n>.uid` in
   the mesh's plan, made once and kept with the board when the plan changes.
3. **The board's key.** Mesh derives the board's key from the two —
   `K_dev = HMAC-SHA256(K_gw, "rh-dev1" ‖ uid)[0:16]` — and writes it into the
   board's build as `src/robohub_secret.h`, which no repository tracks.
4. **The session.** The flashed board says hello with its id; the gateway
   derives the same key, and the two agree on per-session keys for each
   direction. From then on every frame carries a counter and a tag
   ({ref}`secure telemetry <architecture/secure-telemetry>`).

No key crosses a network: Mesh and the gateway each derive the board's key, and
the board has it in its flash. A gateway drops unauthenticated frames unless it
runs with `ALLOW_PLAIN_FRAMES=1`, which is for boards not yet reflashed.

A **relay** — a gateway that reports through another mesh's gateway — is
enrolled the same way, as a board of the parent: it has an id of its own
(`relay_uid` in its plan), and the parent derives its key, which Mesh writes
beside the child as `relay.key`.

Moving a board to another mesh puts it out of date: it has to be built with
that mesh's gateway key and flashed again.

## Hosts: a one-time token

A Linux node that needs a credential of its own enrolls with the keeper using
the `rho bootstrap` component.

### On the keeper's machine

```sh
rho bootstrap token -device garden-01 -project default -area 1 -node 7
```

The token is written to `~/.rho/keeper/enrollment.tokens`. It is for that
device id only, valid for fifteen minutes (`-ttl 1h` for longer) and good for one
enrollment.

### On the node

The node's provisioning file is public configuration — what it is, where it
sits and where the keeper is:

```json
{
  "device": {"id": "garden-01", "kind": "node", "board": "uno-q"},
  "placement": {"project": "default", "area": 1, "node": 7},
  "keeper": {"url": "https://keeper.example.com"},
  "secrets": {"generate": ["instance_id", "identity_key"], "store": "~/.rho/identity"},
  "permissions": {"directory": "0700", "files": "0600"}
}
```

```sh
rho bootstrap init -config /etc/robohub/provisioning.json -token <token>
rho bootstrap status
```

`init` makes an instance UUID and an Ed25519 key pair on the node, in an
owner-only folder, posts the public key and the token to the keeper's
`POST /api/enroll`, and stores the credential it gets back as a `0600` file. A
second run keeps the identity it has (`-force` makes a new one).

The keeper listens on `127.0.0.1` only, so a node on another machine reaches
`/api/enroll` through the TLS proxy in front of the keeper.

### What the keeper checks

- the token exists, is not used and has not expired;
- it was made for this device id;
- a device already enrolled is not taken over by a new token — its credential
  changes only by rotation;
- every field is a plain value (the device id is a name, area and node are
  numbers).

It then keeps the node's record — device, public key, placement, credential —
owner-only under `~/.rho/keeper/nodes/`, and marks the token used.

## The node registry

**Nodes** in the keeper's rail lists the identities it issued. An admin can:

- **rotate** a node's credential — a new one is shown once and the node has to
  take it;
- **revoke** it — the record goes, and the next verification fails.

A gateway or firmware that wants to check a host's credential asks:

```text
POST /api/nodes/verify
device_id=<device>&credential=<credential>
```

and gets back the registered project, area and node, or `403`. The endpoint is
public because the credential is the authentication.

## Not done yet

- No gateway calls `/api/nodes/verify` yet; boards are authenticated by their
  derived keys, as above.
- On a microcontroller, the identity is the key built into its flash. Keeping a
  key in secure storage, flash encryption, enrollment over a link, taking a
  rotated credential and a factory reset that clears the identity belong to the
  firmware and are not implemented. A node that cannot protect its storage has no
  strong identity: whoever reads its flash can be it.
