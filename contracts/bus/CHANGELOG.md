# Changelog

## [0.1.0] - 2026-11-13

The message bus interface: publish to a topic, follow a topic filter, read the
newest message of a topic and the topics heard under a prefix, through the broker
provider an application binds.

## [0.2.0] - 2026-11-13

`relay` publishes every line appended to a file to one topic, and `follow_lines`
appends every payload heard on a filter to a file as it came: a file of lines
carried across the broker unchanged, which is how Mesh's live telemetry feed
reaches an application without an HTTP stream.
