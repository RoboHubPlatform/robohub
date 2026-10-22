# The RoboHub documentation site

The documentation of the RoboHub ecosystem, served as a site.

## What it does

The site collects the documentation every module of the ecosystem ships — the
pages in each module's `docs/` directory, and the API reference generated from
the Rho sources — and serves them together, so that a reader can move from a
platform to the devices on it to the interfaces they implement without leaving
the site.

## Building

```sh
rho build applications/docsite
```

## Running

```sh
./build/docsite
```
