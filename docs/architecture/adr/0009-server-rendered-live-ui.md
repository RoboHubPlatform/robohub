---
id: ADR-0009
title: Server-rendered pages updated over SSE with HTMX
status: proposed
date: 2026-11-08
requirements: [SYS-0025, SYS-0029]
supersedes: []
superseded_by: []
---

# Server-rendered pages updated over SSE with HTMX

## Context

Dashboards must show readings live. A browser-side application that polls or
talks to Mesh would need tokens in the page, duplicate rendering, and a build
pipeline per application.

## Decision

Pages are rendered on the server. A page opens one Server-Sent Events
connection to its application, which sends HTML fragments that HTMX swaps in;
a reconnect starts with a snapshot. The application follows Mesh's feed itself
with its service token and relays what concerns its widgets. Actions are forms
posted to the application, which checks the person's session and forwards the
action to Mesh. Nothing in a browser polls, sees a token, or talks to Mesh or a
gateway; nothing in a page assumes a switch worked until its state comes
back.

## Consequences

- Applications stay small and need no front-end build.
- The server holds one subscription per project, not one per browser.
- Every live element needs a fragment and an event name on the server.
