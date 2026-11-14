# RoboHub Documentation Site

Builds the RoboHub documentation into one static site. It collects the pages
every part of the ecosystem ships — each part's `docs/` directory, or its README
when it has none — into one tree, adds a reference table to each shared module's
page and the release history to each part's, and builds the tree with `rho doc`.
The shape of the site, its sections and their order, is `site.yml`.

## Building

From the root of the `robohub` repository, with the other repositories checked
out beside it:

```sh
rho build applications/docsite
./applications/docsite/build/docsite
```

The tree is assembled in `build/doctree/` and the site is written to
`build/site/`. What each step said is kept under `build/reports/`.

## Serving it

The program builds the site; it does not serve it. Any static file server will,
for example on this machine only:

```sh
python3 -m http.server 8090 --bind 127.0.0.1 --directory build/site
```

and open <http://127.0.0.1:8090/>. Port 8080 is left to the gateway, which uses
it by default.

## Container image

The image carries the built site and serves it with Python's HTTP server on port
8080 inside the container. Build the site first; the image is built from the
repository root, because that is where `build/site/` is:

```sh
cd applications/docsite
rho deploy -target container -docker -build-only
cd ../..
docker run --rm -p 127.0.0.1:8090:8080 <dockerhub-user>/robohub-docsite:latest
```

The `container` target in `targets/container.json` names the Dockerfile
(`deploy/Dockerfile`), the image and the repository root as the build context,
so `rho deploy` run in this folder builds it. `RH_DEPLOY_DOCKER_IMAGE` and
`RH_DEPLOY_DOCKER_TAG` name the image for your own registry account.

## Publishing the image

After rebuilding the site and testing the image:

```sh
(cd applications/docsite && rho deploy -target container -docker -build-only -push)
```
