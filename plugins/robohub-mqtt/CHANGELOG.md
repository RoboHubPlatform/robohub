# Changelog

## [0.1.0] - 2026-11-13

First release: a Mosquitto broker the keeper runs as a user service of its own
on port 1884, beside any broker the system already has, with a broker user and
topic rules for every application that binds the bus and every device an admin
adds; applications reach it through robohub-provider-mqtt.
