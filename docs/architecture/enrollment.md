# Enrolling a node

A gateway accepts readings only from a board it can authenticate, and the keeper
issues credentials only to a node that proved it holds a one-time token. There
are two kinds of identity, for two kinds of node.

| Node | Identity | Made by | Checked by |
|---|---|---|---|
| A board Mesh builds (Pico, ESP32, …) | a device key derived from its gateway's key and its id | Mesh, when it builds the image | the gateway, on every frame, and its node manifest |
| A Linux host | an Ed25519 key pair and a credential the keeper issued | `rho bootstrap` on the node, the keeper's `/api/enroll` | the keeper's `/api/nodes/verify` |
| A Linux host that speaks the board protocol (a gateway node) | both: the keeper credential, used once to fetch a board key from Mesh | `rho bootstrap init -board-key` | as a board, by the gateway |

## Boards: enrolled by being built

Nothing is typed in for a board; its identity is part of its build.

1. **The gateway key.** Each mesh's gateway has a 256-bit key, `K_gw`, made the
   first time it is needed and kept in the mesh's folder as `gateway.key`,
   readable by Mesh's user only. Mesh installs it beside the gateway it starts,
   pushes or deploys, and tells the gateway where it is (`GATEWAY_KEY_FILE`).
2. **The board's id.** Every planned board has a 64-bit id, `node.<n>.id` in
   the mesh's plan (16 hex digits), made by Mesh once and kept with the board
   when the plan changes.
3. **The board's key.** Mesh derives the board's key from the two —
   `K_dev = HMAC-SHA256(K_gw, "rh-dev1" ‖ uid)[0:16]` — and writes it into the
   board's build as `src/robohub_secret.h`, which no repository tracks.
4. **The session.** The flashed board says hello with its id; the gateway
   derives the same key, and the two agree on per-session keys for each
   direction. From then on every frame carries a counter and a tag
   ({ref}`secure telemetry <architecture/secure-telemetry>`).

No key crosses a network: Mesh and the gateway each derive the board's key, and
the board has it in its flash. A gateway drops unauthenticated frames; on the
serial link only, `ALLOW_PLAIN_FRAMES=1` accepts plain ones while boards are being
reflashed. The uplink never takes a plain frame.

The folders Mesh builds boards in, and the images it builds there, hold the
board's key (and the Wi-Fi password in `project.conf`): Mesh keeps its whole
tree readable by its own user only — folders `0700`, the generated
`robohub_secret.h`, `project.conf` and the built `.elf`/`.uf2` `0600` — and closes
anything an older version left readable when it starts.

### The node manifest

A derived key proves a board was keyed for this gateway, not that it still
belongs to it or where it sits. Mesh therefore writes a **node manifest**,
`nodes.txt`, beside `gateway.key` in the mesh's folder: whenever the plan
changes (a board added, moved, deleted, revoked or admitted again, a mesh linked
below), and at every gateway start, which copies it to the gateway's host with
the key. It is written whole (a temporary file and a rename), `0600`, one line
per node:

```text
# uid|area|node|role|epoch|revoked|areas
0123456789abcdef|1|4|board|0|0|
1111222233334444|1|2|relay|0|0|
9999aaaabbbbcccc|7|0|relay|0|0|7,8
```

`uid` is `node.<n>.id`, `area` and `node` the board's placement, `role` `board` or
`relay`, `epoch` the key epoch (`0`; not read yet), `revoked` `0` or `1`, and
`areas`, for a relay, the areas it may announce. A board the plan gives the role
`relay` carries boards in the mesh's own area, which speak for themselves, so it
announces nothing; a mesh linked below is a relay for its own area and every
area below it. Modules and devices open no session and are not listed.

With a manifest, the gateway answers a hello only from a listed board that is
not revoked, takes a board's readings only for its own area and node, and takes
an announce only from a relay for its own areas — never for the gateway's own
area. Without one (a gateway deployed before Mesh wrote it) it says so once and
accepts any board whose key derives.

### Revoking a board

A board that is lost, stolen or replaced is taken out without re-keying the
mesh: **Revoke** in the board's inspector in Mesh sets `node.<n>.revoked` in the
plan and rewrites the manifest. A gateway on Mesh's machine reads the file again
within seconds; one deployed to another host over SSH or ADB is sent the new
file at once (if that fails, Mesh says so and the next gateway start sends it).
The gateway then refuses the board's hello and drops its sessions. **Admit it
again** undoes it; the board's key was never changed.

On the gateway's host every secret file — `gateway.key`, `relay.key`,
`nodes.txt` — is created by the remote shell under `umask 077` before anything is
written to it (over SSH it is streamed in and renamed into place), so it is never
readable by another user, not even for a moment.

A **relay** — a gateway that reports through another mesh's gateway — is
enrolled the same way, as a board of the parent: it has an id of its own
(`relay_uid` in its plan), and the parent derives its key, which Mesh writes
beside the child as `relay.key`. In the parent's manifest it is a `relay` for its
own area and the areas below it.

Moving a board to another mesh puts it out of date: it has to be built with
that mesh's gateway key and flashed again.

## Hosts: a one-time token

A Linux node that needs a credential of its own enrolls with the keeper using
the `rho bootstrap` component.

### On the keeper's machine

```sh
rho bootstrap token -device garden-01 -project default -area 1 -node 7
```

The token is added to `~/.rho/keeper/enrollment.tokens` as one line,
`token|device|project|area|node|expires|flags`. It is for that device id only,
places the device at that project, area and node, is valid for fifteen minutes
(`-ttl 1h` for longer) and is good for one enrollment. The keeper marks tokens
used in the same file, so `rho bootstrap token` adds its line under the keeper's
lock (the directory `enrollment.tokens.lock`) and replaces the file whole through
a temporary file and a rename: a token added while the keeper spends another is
not lost. `-reenroll` makes a token that may replace a device that is already
enrolled.

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
rho bootstrap init -config /etc/robohub/provisioning.json -token-file /run/enroll.token
rho bootstrap status
```

The token is read from a file, or from standard input with `-token-file -`; a
token on the command line (`-token`) is refused, because every user of the
machine can read a command line. The keeper URL must be `https://` — plain
`http://` is accepted only for `127.0.0.1` or `localhost` — and redirects are not
followed.

`init` makes an instance UUID and an Ed25519 key pair on the node, in an
owner-only folder, posts the public key and the token to the keeper's
`POST /api/enroll`, and stores the credential it gets back as a `0600` file. A
second run keeps the identity it has (`-force` makes a new one). The placement in
the provisioning file is sent only to be compared: the node is recorded where its
token places it.

The keeper listens on `127.0.0.1` only, so a node on another machine reaches
`/api/enroll` through the TLS proxy in front of the keeper.

### What the keeper checks

- the token exists, is not used, names a device and an expiry, and has not
  expired — a token without a device or without an expiry is refused;
- it was made for this device id;
- the placement is the token's: a request that names another project, area or
  node is refused, and one that names none is placed where the token says;
- a device already enrolled is not taken over: only a token made with
  `-reenroll` replaces it, otherwise its credential changes only by rotation;
- every field is a plain value (the device id is a name, area and node are
  numbers).

Finding the token, checking it, writing the node's record and marking the token
used are one step under the token file's lock, so one token presented many
times at once enrolls once. The record — device, public key, placement and the
credential as a salted hash (`s1$<salt>$HMAC-SHA256(salt, credential)`), never the
credential itself — is kept `0600` under `~/.rho/keeper/nodes/` (`0700`).
Records an older keeper kept in the clear are hashed when the keeper starts.

`/api/enroll` and `/api/nodes/verify` need no session, so each has a budget of
calls per client and one for all clients together (enrollment 10 a minute per
client, verification 60; 429 past it). The client is the address the TLS proxy
in front of the keeper appended to `X-Forwarded-For`.

## The node registry

**Nodes** in the keeper's rail lists the identities it issued. An admin can:

- **rotate** a node's credential — a new one is shown once (and kept only as a
  hash) and the node has to take it;
- **revoke** it — the record goes, and the next verification fails.

Revoking a host's keeper record stops it fetching its board key again; a board
key it already holds is taken out of the mesh with **Revoke** in Mesh, as for a
board.

A gateway or firmware that wants to check a host's credential asks:

```text
POST /api/nodes/verify
device_id=<device>&credential=<credential>
```

and gets back the registered project, area and node, or `403`. The endpoint is
public because the credential is the authentication; the comparison takes as
long whatever matched.

## Host nodes that speak the board protocol

A Linux host that runs a node of the board protocol (`robohub-device-node`, a
gateway node) needs a board id and key, as a flashed board does, but it is not
flashed. It gets them with its keeper credential, so every node has one identity
scheme:

```sh
rho bootstrap init -config /etc/robohub/provisioning.json -token-file /run/enroll.token -board-key
rho bootstrap key        # later, again: the same id and key
```

After enrolling, `rho bootstrap` posts to Mesh's node-key endpoint through the
keeper's origin, over HTTPS:

```text
POST <keeper>/app/mesh/mesh/api/nodes/key
Authorization: Node <device>:<credential>
→ { "ok": true, "uid": "<16 hex>", "key": "<32 hex>", "project", "area", "node" }
```

Mesh asks the keeper on the loopback (`/api/nodes/verify`) whom the credential
belongs to, finds the board planned at that placement — the project the keeper
recorded, or the one mesh with that area — and answers its id and `K_dev`. A
revoked board, a placement with no board planned and a credential the keeper
refuses get nothing; the key is never logged, and a client may ask ten times a
minute. The node keeps them as `board.key` (the key) and `board.env`
(`RH_SECURE_UID`, `RH_SECURE_KEY_FILE`) in its identity folder, both `0600`; a
systemd unit reads `board.env` as its environment file. The board must be
planned in Mesh at the token's area and node before the key can be fetched.

## Not done yet

- No gateway calls `/api/nodes/verify`; boards, host nodes included, are
  authenticated by their derived keys and the node manifest, as above. Mesh calls
  it, to hand a host node its board key.
- Mesh asks the keeper from its own loopback, so the keeper counts those calls
  against one client; Mesh's own budget per client is what bounds them.
- Keys are not rotated: the manifest's `epoch` is always `0`.
- On a microcontroller, the identity is the key built into its flash. Keeping a
  key in secure storage, flash encryption, enrollment over a link, taking a
  rotated credential and a factory reset that clears the identity belong to the
  firmware and are not implemented. A node that cannot protect its storage has no
  strong identity: whoever reads its flash can be it.
