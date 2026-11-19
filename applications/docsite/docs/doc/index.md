# The RoboHub documentation site

The documentation of the RoboHub ecosystem, built as one static site.

## What it does

The program collects the documentation every part of the ecosystem ships — the
pages in each part's `docs/doc/` directory (or `docs/`, where a part has not
moved its pages there), or its README when it has neither — into one tree,
sorts the parts into the sections `site.yml` names (Overview, Get started, How
it fits, Applications, Build an application, Integrations, Devices & firmware),
appends a generated reference to each shared module's page and the
release history to each part's, and builds the tree with `rho doc`. A reader can
move from an application to the modules it is built from, the interfaces they
use and the devices behind them without leaving the site.

## Building

From the root of the `robohub` repository:

```sh
rho build applications/docsite
./applications/docsite/build/docsite
```

The tree is assembled in `build/doctree/` and the site is written to
`build/site/`. Both can be named — `docsite <tree> <site>` — so a check can
assemble and build into a scratch folder and leave `build/site/` alone:

```sh
./applications/docsite/build/docsite /tmp/tree /tmp/site
(cd /tmp/tree/robohub && ROBOHUB_WORKSPACE= rho req check --workspace)
```

In the tree each part of this repository (a module, a provider, a contract, a
plugin, the protocol) is a folder named as `rho req` names it — its
`requirements: name:`, else its module name: `robohub-alert`,
`robohub-provider-email`, `robohub-gateway-contract` — so the tree's
requirements and the references between them read as they do in the
repositories. `tests/tree_names.sh` checks it.

## Serving it

The program does not serve the site. Any static file server will:

```sh
python3 -m http.server 8090 --bind 127.0.0.1 --directory build/site
```

Port 8080 is left to the gateway, which uses it by default.
