# RoboHub Documentation Site

Serves the RoboHub documentation as a static site. Collects the documentation
every module of the ecosystem ships — the pages in each module's `docs/`
directory — and builds them into one site, so that a reader can move from a
platform to the devices on it to the interfaces they implement without leaving
the documentation.

## Building

```sh
rho build applications/docsite
./applications/docsite/build/docsite
```

The documentation is assembled into `build/doctree/` and the site is written to
`build/site/`.

## Running

```sh
python3 -m http.server 8080 --directory build/site
```

## Image

The image carries the built site and serves it with Python's HTTP server on port
8080. It is built from the repository root, because that is where `build/site/`
is:

```sh
docker build -f applications/docsite/deploy/Dockerfile -t miraur/robohub-docsite:latest .
docker run --rm -p 8080:8080 miraur/robohub-docsite:latest
```

## Deploying

The image is published to Docker Hub as `miraur/robohub-docsite:latest`, after
the site has been rebuilt and the image tested:

```sh
docker push miraur/robohub-docsite:latest
```
