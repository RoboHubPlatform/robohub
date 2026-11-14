# A gateway, boards and devices

Readings reach the applications through **Mesh**: it plans a mesh — a gateway
and what reports through it — builds and flashes the boards, runs the gateway
and keeps every reading. This page goes from nothing to a reading on a
dashboard. Mesh's own guide, {ref}`mesh/index`, has the rest.

## 1. Install Mesh

Install Mesh from the keeper as any other application ({ref}`start/applications`)
and open it: **Open application**, or `http://127.0.0.1:19090/app/mesh/mesh`.
Its front page is the **fleet**: every mesh it manages.

## 2. Make a mesh

On the fleet, **+ New mesh** takes a name. The mesh gets a folder of its own
(under `~/.rho/mesh/projects/`), an area, a REST port and an uplink port, so two
meshes run side by side on one machine.

The mesh opens as its **agora** — the live tree, an inspector beside it — with
three prompts:

1. **Choose where the gateway runs.** *This host (native)* runs the gateway as
   a process on the keeper's machine. A board that can be a gateway, or another
   Linux host reached over SSH or ADB, is chosen from the list; the list comes
   from the boards' own manifests. The gateway's inspector sets its ports and
   builds, starts and stops it.
2. **Add the first node.** **+ node** on the gateway: a board, the link it
   reaches the gateway over (UART, USB, Wi-Fi, …, whatever both ends support)
   and its modules — the sensor boards fitted to it.
3. **Apply.** **Apply changes** lists what differs from what runs, then builds
   each changed board, starts the gateway and asks you to put each board in its
   programming mode to flash it (for a Pico 2 W: hold BOOT, tap RST, release
   RST, then BOOT).

Builds and flashes are jobs; the activity strip shows what runs and what failed,
and a job's log opens in the inspector. When a board runs what is planned its
card stops showing *out of date*, and its readings appear on it.

## 3. What makes a board trusted

Every frame between a board and its gateway is authenticated. Mesh makes a key
for each gateway, kept in the mesh's folder and readable by Mesh's user only,
and gives every planned board an id; the board's own key is derived from the
two and built into its firmware. A board built by Mesh is therefore enrolled by
being built — there is nothing else to do. A board that sends unauthenticated
frames is dropped unless the gateway runs with `ALLOW_PLAIN_FRAMES=1`.

A Linux host that should be a node with an identity of its own — a credential
the keeper issued — is enrolled with a one-time token instead:

```sh
# on the keeper's machine
rho bootstrap token -device garden-01 -project default -area 1 -node 7
# on the node, with the keeper's URL in its provisioning file
rho bootstrap init -config /etc/robohub/provisioning.json -token <token>
```

The token is good for fifteen minutes (`-ttl` changes that) and for one
enrollment. The keeper's **Nodes** page lists the identities it issued, and
rotates or revokes them. {ref}`architecture/enrollment` explains both kinds of
identity.

## 4. A gateway on another machine

A gateway on another host is reached over the network, and every request Mesh
makes to it carries a short-lived token scoped to that gateway alone
(`gateway:<mesh>:*`). To keep the tokens off the network in the clear, give the
gateway a certificate: set `gateway_tls_cert` and `gateway_tls_key` — paths on
the machine the gateway runs on — in the mesh's `plan.yml`, and its
`gateway_url` becomes an `https://` address.

A mesh can also report **through** another mesh: in its gateway's inspector,
**Reports through** names the parent, and its gateway runs as a relay that dials
the parent gateway's uplink.

## 5. MQTT devices

A network device that speaks MQTT — a Shelly Plug M Gen3, for instance —
reports through a broker the keeper runs, the **MQTT** integration
(`robohub-mqtt`, Mosquitto on port 1884):

1. **Run the broker.** In the keeper, **Applications → Integrations → MQTT →
   Run it**. It needs `mosquitto`, which its Dependencies tab can install.
   Every application whose manifest binds the bus — Mesh, Aquarium, Energy —
   becomes a broker user with its own password and the topics its manifest
   names. Restart those applications once after the broker first runs, so they
   are started with its address.
2. **Add the device.** On the broker's page, **Clients → Add the device**: a
   name and the topic prefix it may write and read under (`shelly-plug-1`). The
   password is shown once.
3. **Let it in.** The broker listens on this machine only. For a device on the
   network, **Open it to the network, for devices** on the same tab.
4. **Configure the device** with the broker's address (`192.168.1.20:1884`),
   the user and password from step 2, and the same topic prefix.
5. **Add it to the mesh.** In Mesh, **+ device** on the gateway: choose the
   integration, the transport `mqtt`, and the topic prefix as its address.

The broker's **Topics** tab shows what it carries, live, so a device that
connected is visible before Mesh reads it. An HTTP device is added the same way
with the transport `http` and its address, and Mesh polls it.

## 6. Read it in an application

Aquarium and Energy read Mesh through the gateway interface. Started by the
keeper, they are told where Mesh is and get a token for it on their own; their
**Settings → Gateway** chooses the mesh (the *project*). Each source a mesh
publishes — a board's temperature, a plug's power — can then feed a dashboard
widget, a rule or an equipment role.

Without a mesh, the same Settings tab switches an application to its simulator,
which serves the devices its presets describe.

## Next

- {ref}`architecture/reading` — the path one reading takes.
- {ref}`architecture/security` — sign-in, tokens and what each part may do.
