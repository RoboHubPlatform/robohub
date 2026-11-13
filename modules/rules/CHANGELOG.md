# Changelog

## [0.1.0] - 2026-11-13

The rule engine RoboHub applications share. Conditions in a small fixed grammar
(comparisons of inventory readings, host values and literals; and, or, not,
brackets; the mode in force; a time window), actions on inventory items, alerts,
the journal and modes, and a state machine per rule with a pending window, a
clear condition and a cooldown. Modes run actions, suspend rules and end by
themselves. Rules and modes are seeded from an application's presets; a page and
a JSON API.

A rule whose action could not be done stays where it was and tries again, rather
than counting as fired; the problem is written to the journal once, not on every
evaluation.
