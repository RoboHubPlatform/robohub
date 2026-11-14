# Installing RoboHub

RoboHub runs on a Linux machine with systemd — a small server, a desktop or WSL
on Windows. Installing it means installing the Rho toolchain, checking out two
repositories, and starting the keeper, which installs everything else.

## What you need

| | Why |
|---|---|
| Linux with systemd and a user session (`systemctl --user`) | the keeper and every application run as systemd user units |
| Go | Rho compiles every RoboHub application to Go |
| `git`, `curl`, `flock` | the keeper clones applications, asks them for their health, and runs one job at a time per application |
| The Rho toolchain | builds the keeper and the applications, signs people in (`rho auth`), checks the machine (`rho doctor`) |

The keeper's **Dependencies** page checks all of this again once it runs, and
says what is missing.

## 1. Install Rho

Install the toolchain as [its own guide](https://rho-lang.org/install)
describes: build `rho` from a checkout and run `rho install`, which puts it in
`~/.rho/bin`. Then install the components, which the keeper runs as commands —
`rho auth`, `rho doctor`, `rho keeper` and `rho artifact` among them. From the
Rho checkout, its own script builds and installs every component it carries:

```sh
./scripts/check.sh
```

Check that the toolchain answers:

```sh
rho version
rho help          # lists the commands this machine can reach: auth, doctor, keeper ...
```

## 2. Check out RoboHub

The keeper and the shared modules it is built from live in two repositories,
which are checked out side by side in one folder — the *workspace*:

```sh
mkdir -p ~/robohub-workspace && cd ~/robohub-workspace
git clone https://github.com/RoboHubPlatform/robohub
git clone https://github.com/RoboHubPlatform/robohub-keeper
```

The keeper finds the `robohub` checkout beside its own. When it is somewhere
else, `ROBOHUB_ROOT` names it.

## 3. Start the keeper

The keeper normally runs as a user service, which its deploy script installs:

```sh
cd ~/robohub-workspace/robohub-keeper
./scripts/deploy-keeper.sh
```

The script:

1. builds the keeper with `rho build .`;
2. makes a release of the build under `~/.rho/keeper/apps/keeper/releases/`
   and points `~/.rho/keeper/apps/keeper/current` at it (the three newest are
   kept);
3. creates the keeper's own folder, `~/.rho/keeper`, readable by your user only;
4. writes the unit `~/.config/systemd/user/robohub-keeper.service`, enables
   lingering for your user so it runs without a login, and restarts it.

The log of every deploy is `~/.rho/keeper/deploy.log`. To see whether the
service runs, and which release:

```sh
./scripts/deploy-keeper.sh --status
```

Run the script again after updating the checkout: the service runs the release,
never the checkout's build, so nothing changes until the next deploy.

### Trying it without a service

To run the keeper in the foreground instead — to try it, or while working on
it — build it and start it through the `robohub` command:

```sh
cd ~/robohub-workspace/robohub
rho build ../robohub-keeper
rho build .
./build/robohub keeper            # http://127.0.0.1:19090/
```

`./build/robohub keeper 19091` uses another port. The keeper's output is kept
in `build/reports/keeper.txt`.

## 4. Open it

Open <http://127.0.0.1:19090/> in a browser on the same machine. The first
sign-in is described in {ref}`start/first-run`.

The keeper listens on `127.0.0.1` only. It signs people in over plain HTTP, so
it is not opened to the network by default:

- **From another computer**, forward the port over SSH and open the same
  address there:

  ```sh
  ssh -L 19090:127.0.0.1:19090 user@192.0.2.10
  ```

- **For a permanent address on your network**, put it behind a reverse proxy
  that terminates TLS. `KEEPER_LISTEN=0.0.0.0 ./scripts/deploy-keeper.sh` makes
  the service listen on every interface, which is only safe behind such a proxy
  or on a network you trust.

Under WSL, a browser on Windows reaches `127.0.0.1:19090` in WSL directly.

## Next

- {ref}`start/first-run` — the access token, your account and the people who
  sign in.
- {ref}`start/applications` — installing Mesh, Aquarium and Energy.
