# The RoboHub documentation site

The documentation of the RoboHub ecosystem, served as a site.

## What it does

The site collects the documentation every module, application and plugin of the
ecosystem ships — the pages in each `docs/` directory, and the API reference
generated from the Rho sources — and serves them together, so that a reader can
move from a platform to the devices on it to the interfaces they implement,
then to the applications and modules built on top, without leaving the site.

## Building

```sh
rho build applications/docsite
```

## Running

```sh
./build/docsite
```
