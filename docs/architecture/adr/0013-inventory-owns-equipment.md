---
id: ADR-0013
title: Inventory owns equipment and its bindings to gateway sources
status: proposed
date: 2026-11-13
requirements: [SYS-0025]
supersedes: []
superseded_by: []
---

# Inventory owns equipment and its bindings to gateway sources

## Context

Rules, widgets and schedules need to name the heater, not the smart plug that
happens to switch it. The aquarium and energy each had their own equipment
pages, and a separate equipment module was proposed beside the inventory.

## Decision

The shared inventory is the single module for consumables, parts and
equipment, with categories defined per application. An equipment item has a
handle, and its capabilities (switch, power, temperature, …) are bound to
gateway sources on the inventory's Devices page; the rest of an application
refers to `handle.capability`. What differs per application is asked through
`host_devices_*` functions.

## Consequences

- Replacing a plug is one binding change; rules and widgets stay as they are.
- Rules are per application; the rule engine is shared.
- The inventory module now carries migrations for both applications' data.
