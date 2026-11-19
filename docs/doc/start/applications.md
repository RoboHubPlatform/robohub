# Installing and running applications

The keeper installs the applications, runs them and keeps them up to date. Every
step here is on the keeper's pages and needs an admin, except starting and
stopping, which an operator may do too.

## Install one

On the keeper's home page, choose **Install an application**. It offers three
ways in:

| Source | What happens |
|---|---|
| **From the Rho registry** — `aquarium`, or `aquarium@0.6.10` for a particular version | the keeper runs `rho module install` and runs the application as it was published |
| **Found on this machine** — applications in the workspace, the module registry or the orchestrator that the keeper does not run yet | the folder is added where it is, not moved or copied |
| **A git URL or a folder** | a URL is cloned into `~/.rho/apps/<name>` (`ROBOHUB_APPS_HOME`); a folder with a `module.yml` stays where it is |

Before anything is installed, the keeper shows what the application needs:

- **the machine** — the programs its manifest's `system_deps` names, as
  `rho doctor` finds them. A required program that is missing stops it from
  starting; **Install** on its row fetches it into `~/.rho/toolchains` or uses
  the package manager;
- **Rho modules** it depends on outside RoboHub's own;
- **other applications** it depends on and the services it calls — Aquarium and
  Energy call Mesh, for instance.

Mesh, Aquarium and Energy are installed the same way. Install Mesh first: the
other two read their devices through it, or through their simulator until there
is one.

## How an application runs

Each application is a **systemd user unit** the keeper writes from the
application's manifest: it restarts on failure, starts after the applications it
depends on, and reads its environment from an owner-only `app.env` — its name,
its workspace, the address to listen on, a secret of its own, where the keeper
is, and the credential it calls other services with.

| | Where |
|---|---|
| Listens on | `127.0.0.1:<port>` — the port in its manifest (Mesh 8478, Aquarium 8480, Energy 8482), or the next free one from 8500 when another application has it |
| Its data and settings | its workspace, `~/.rho/keeper/workspaces/<name>/` |
| What runs | for an application built from a folder, a release: `~/.rho/keeper/apps/<name>/releases/<version>-<time>`, with `current` pointing at the one in use; a published package runs where it was installed |
| Its log | **Log** on its row (the unit's journal), and the rotating file `~/.local/state/robohub/<name>/app.log` its Logging settings describe |

The keeper's home page shows each application as a card, with its state from
systemd and its `/healthz`: *running*, *starting*, *failed*, *stopped*, *not
built* or *no service yet*. Selecting a card opens its inspector: start, stop,
restart, build, redeploy, roll back, its dependencies, its journal and its
environment.

Building and redeploying are **jobs**: they run in the background, one at a time
per application, and the strip at the bottom of every page shows what is running
and how the last job ended. **Jobs** in the rail lists them with their logs.

An application can listen on the network instead of `127.0.0.1` only when its
manifest says `deploy.listen: lan`.

## Reach one

**Open application** opens it through the keeper, at
`http://127.0.0.1:19090/app/<name>/` — Mesh at `/app/mesh/mesh`, Aquarium at
`/app/aquarium/`. Every application is reached on the keeper's own address, so a
remote browser or a reverse proxy needs only the keeper's port, and the
keeper's session cookie is never passed to an application. The first visit
signs you in through the keeper and back.

The keeper's switcher in the top bar of every application leads from one to the
next. **Add to menu** puts an application under **Applications** in the
keeper's rail.

To link to the applications' own ports instead of the proxy, set
`keeper.proxy_apps=off` in the keeper's settings file,
`~/.rho/keeper/data/settings.conf`.

## Update, redeploy, roll back

| Action | What it does |
|---|---|
| **Update to …** | for an application from the Rho registry: shown when the registry has a newer version (asked at most once an hour). It installs that version, points the keeper at it and restarts; the old version stays installed. |
| **Build** | `rho build` in the application's folder. Nothing running changes. |
| **Redeploy** | builds, makes a new release, writes the unit again and restarts. A build that fails leaves the running release alone. |
| **Restart** | restarts the release in use. A unit that no longer matches the application — a moved folder, a new port — is written again first. |
| **Roll back** | puts the release before the one in use back in use and restarts. The three newest releases are kept, so a second rollback goes one further back. |

After pulling new code into a checkout, **Redeploy** is what puts it in use.

## Remove one

**Uninstall** stops the application and removes its unit and its record. Its
folder is deleted only when the keeper cloned it; a checkout or a package is left
alone and offered again under *found on this machine*.

## Next

{ref}`start/gateway` — a gateway, boards and devices for the applications to
read.
