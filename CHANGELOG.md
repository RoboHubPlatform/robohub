# Changelog

All notable changes to this module are recorded here, one section per release.
A module's description says what it is and does not change between releases; this
says what changed, which is what tells two versions of one module apart. The
section for the version being published travels with it, so a registry shows it
against that version.

## [0.1.0] - 2026-10-21

The orchestrator of the RoboHub ecosystem: a registry of its modules, and the
tools that run over all of them.

The registry names every module of the ecosystem, where it is and what it is for,
and each module's own manifest remains the truth about what it is. The
orchestrator reads the manifests it needs and repeats nothing.

The tools are the toolchain's own components — the linter, the test runner and
the documentation generator — run over each module in turn, and what each said
is written to `build/reports/`. The orchestrator decides what to run them over
and collects what they said; the components decide how to run and what their
findings mean.

The material every repository in the ecosystem needs and none of them should own
is here as well: the ignore rules, the configuration a CI build resolves, and
the workflow itself, as a workflow the repositories call rather than a copy
each of them carries.
