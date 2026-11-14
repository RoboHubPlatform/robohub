# Security

Everything runs as your user on one machine, so the boundaries that matter are
between people, between programs, and between the machine and the network. This
page says what each one is and where it is enforced.

## What is open to the network

| What | Listens on | To reach it from elsewhere |
|---|---|---|
| Keeper | `127.0.0.1:19090` | an SSH tunnel, or a TLS reverse proxy (`KEEPER_LISTEN` opens it, for use behind one) |
| Applications | `127.0.0.1:<port>` | through the keeper, at `/app/<name>/`; an application listens on the network only when its manifest says `deploy.listen: lan` |
| MQTT broker | `127.0.0.1:1884` | an admin opens it to the network for devices; nobody connects without a broker user |
| A gateway | its REST and uplink ports | Mesh's tokens; HTTPS when the mesh names a certificate (`gateway_tls_cert`, `gateway_tls_key`) |

## Signing in

The keeper is the only issuer. It holds one ES256 (P-256) signing key and
publishes the public key at `/auth/public-key`; nothing else reads its key.

- **People.** `~/.rho/keeper/users.yml`, owner-only, kept by `rho auth`, which
  hashes passwords with PBKDF2. The keeper hands a password over in a private
  file it removes at once, never on a command line. Five wrong attempts in a
  row close the sign-in for that name for five minutes.
- **The access token** in `~/.rho/auth/master.token` is the admin's way in on
  the first run and afterwards. Changing it asks for the current one and signs
  out every other session.
- **Tickets.** Signing in to an application sends the browser to the keeper and
  back with a ticket: signed with the keeper's key, for that application's
  audience and redirect address, used once, valid for thirty seconds, carrying
  the person's name and only their grants for that application.
- **Application sessions.** The application verifies the ticket with the public
  key and keeps a session of its own in a cookie named for it
  (`rho_session_<app>`), valid for at most eight hours. It asks the keeper at
  most once a minute whether the keeper session it came from is still open, so
  signing out of the keeper — or *Sign out everywhere* — ends it. A keeper that
  cannot be reached signs nobody out.
- **Rotating the key** (*Recovery token → Rotate the signing key*) stops every
  ticket and token signed with the old key at once; applications fetch the new
  public key when they first see it used.

## Roles, grants and scopes

A person's **role** — admin, operator or viewer — is what they may do in the
keeper. Their **grants** are scopes for each application: `mesh:*`,
`mesh:greenhouse`, `mesh:read`, `aquarium:read`. An admin's tickets carry `*`.

Programs calling each other use **service tokens**. The keeper registers each
application as a client for the services its manifest calls (`deploy.calls`),
and starts it with a client id and the path of its secret
(`RHO_CLIENT_ID`, `RHO_CLIENT_SECRET_FILE`). The runtime exchanges the
credential for a token:

```text
POST /auth/service-token   client_id, client_secret, audience, scopes
→ { token, expires_in }    ES256, for that audience and those scopes, at most ten minutes
```

and keeps it until 80 % of its lifetime has passed. The callee verifies it
offline with the public key.

| Caller → callee | Audience | Scope |
|---|---|---|
| An application → Mesh | `mesh` | `mesh:<project>` — the mesh it reads |
| Mesh → a gateway | `gateway` | `gateway:<project>:*` — that gateway only |
| Mesh → a service that is a mesh's gateway (Energy) | `<audience>` | `<audience>:gateway` |
| An application → the keeper's API | `keeper` | `keeper:read` |

**Per-gateway scopes.** A gateway knows its own id (`GATEWAY_ID`, the mesh's
name) and accepts `gateway:<id>:read` for telemetry, the outbox and diagnostics,
and `gateway:<id>:command` for switching, commands and devices;
`gateway:<id>:*`, `gateway:*` and `*` hold both. Mesh may be issued `gateway:*`,
but asks each gateway's token for `gateway:<project>:*`, so a token captured on
the network opens that gateway and no other, for minutes. There is no static
gateway token.

**Every relying party** — the keeper, each application, each gateway — is
generated with Rho's auth middleware, which removes `X-Rho-Subject`,
`X-Rho-Scopes` and `X-Rho-Aud` from every request before anything else and sets
them only from a token it verified; refuses a token for another audience; and
refuses a token whose id is in the revocation list `rho auth revoke --jti`
writes.

## The proxy

The keeper serves each application at `/app/<name>/` (the `app_proxy`
middleware), on loopback to its port. Cookies are scoped by host, not by port,
so applications on ports of their own would each receive every other one's
cookies — the keeper's admin session among them. Behind the proxy:

- the keeper's own cookie (`keeper_session`) is never forwarded;
- an application's cookies are rewritten to its own path;
- links, redirects and cookie paths are rewritten onto the prefix, and
  `X-Forwarded-Prefix`, `-Host` and `-Proto` tell the application where it is
  reached;
- event streams are relayed as they are written.

The proxy does not sign anyone in; each application does, through the keeper,
as above. Forms posted from another origin are refused by every application
(`same_origin`), because the keeper and the applications are the same host,
which a `SameSite` cookie does not tell apart.

## Isolation between applications

All applications run as the same user, so the keeper isolates them with
systemd. Every unit it writes has `NoNewPrivileges=yes`. Where the machine's
systemd can give a user service a private view of the file system — the keeper
tries once and remembers (`~/.rho/keeper/isolation.txt`) — an application also
gets:

- `~/.rho/keeper` as an empty, read-only folder, with only its own workspace
  and its own releases put back;
- the signing key, the access token, the client credentials and the client
  registry made inaccessible.

So an application cannot read another application's workspace, the people
store, or anything that mints tokens. Integrations, such as the MQTT broker,
run their own program with `NoNewPrivileges` only.

Each application also gets a random secret of its own (`RHO_APP_SECRET`), the
seed of its forms' CSRF tokens.

## Secrets on disk

| Secret | Where | Mode |
|---|---|---|
| Signing key, access token, client credentials | `~/.rho/auth/` | owner-only |
| The keeper's state: sessions, people, catalogue, jobs | `~/.rho/keeper/` | folder `0700` |
| An application's environment, including its client secret path | `~/.rho/keeper/workspaces/<name>/app.env` | owner-only |
| An application's broker password | its workspace | owner-only |
| Broker users | hashed by `mosquitto_passwd` from an owner-only file | — |
| A gateway's key | `<mesh>/gateway.key`, and `GATEWAY_KEY_FILE` beside the gateway | readable by its user only |
| A board's key | `src/robohub_secret.h` in its generated build | never in a repository |
| Enrollment tokens and node records | `~/.rho/keeper/enrollment.tokens`, `~/.rho/keeper/nodes/` | `0600` |
| A host node's identity and credential | `~/.rho/identity/` | `0700` / `0600` |

Secrets never pass through a report file or a command line: every program the
keeper runs gets its arguments one per line, so a name or a URL is exactly one
argument, and a value with a line break or a leading `-` is refused.

## Boards and gateways

Frames between a board and its gateway are authenticated, fresh and bounded in
time, but not encrypted: readings and commands are not secret, but they must not
be forged or replayed. See {ref}`architecture/enrollment` for the keys and
{ref}`secure telemetry <architecture/secure-telemetry>` for the frame.

## Updates

A signed artifact placed in `~/.rho/keeper/incoming/` is used by **Redeploy**
only when it verifies against `ROBOHUB_ARTIFACT_PUBKEY` (Ed25519); a failed health
check after the switch restores the previous version.
`ROBOHUB_ARTIFACT_ALLOW_UNSIGNED=1` accepts a checksum alone, for a development
machine.
