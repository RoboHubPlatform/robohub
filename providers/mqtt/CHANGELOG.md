# Changelog

## [0.1.0] - 2026-11-13

The MQTT provider of the bus interface: publishes at QoS 1, follows a filter in
the background with the newest message per topic, through the RoboHub platform's
mqtt port, with the broker the keeper gave the application unless the binding
names another.

## [0.2.0] - 2026-11-13

Implements `relay` and `follow_lines` of robohub-bus 0.2.0 through the mqtt
port's `mqtt_relay` and `mqtt_follow_lines` (rho-robohub 0.5.0).
