# How a change is made

Every change to RoboHub starts from a requirement and ends with a test that
proves it. Between the two sit the decisions that shaped it and the code that
does it, and each is linked to the next, so that for any line of code you can
ask *why is this here* and for any requirement *how do we know it holds* — and
a tool answers, not a person's memory.

This page is the process. The tool that checks it is `rho req`, part of the Rho
toolchain, so the same process works in any Rho repository; the keeper's
Developer section is where it is maintained day to day.

## What is written down

| Artefact | Where | What it says |
|---|---|---|
| **Requirement** | `docs/requirements/**/*.yml` in each repository | What must be true, testably, and which higher requirement it serves |
| **Architecture decision (ADR)** | `docs/architecture/adr/NNNN-slug.md` | One decision: its context, what was decided, what it costs, which requirements it serves |
| **Implementation** | the code, tagged `// @req ID` | Where a requirement is met |
| **Verification** | the tests, tagged `// @verifies ID` | What proves it, and whether the last run passed |

The prose about the architecture — how the parts fit, the security model, the
network — is ordinary documentation and lives with the other pages in
`docs/doc/architecture/`; `docs/doc/` holds every page a reader browses, and
`docs/requirements/` and `docs/architecture/` beside it hold only the process's
artefacts. ADRs record the individual decisions behind the prose, so a later
change can replace one decision without rewriting the picture.

## Levels

Requirements are written at levels, from the system down. The levels are
declared once, for the whole ecosystem, in `robohub/docs/requirements/levels.yml`:

| Level | Says | Example |
|---|---|---|
| **SYS** | What RoboHub does for the person running it | *A board keeps reporting after the gateway restarts, with no one touching it.* |
| **NODE** | What one repository does towards that | *The gateway re-establishes every enrolled board's session within 30 s of a restart.* |
| **SUB** | What one subsystem inside a repository does | *The keeper's sign-in issues a ticket bound to one application's callback.* |
| **UNIT** | What one module or function does | *`auth_target_ok` refuses a callback on another port.* |

A requirement serves one or more requirements of a **higher** level
(`satisfies:`), never the same or a lower one. A small repository may use only
NODE; a repository that is a subsystem in its own right — the keeper, Mesh —
uses as many levels as it needs, in as many files as it needs.

SYS requirements live in `robohub`. Each other repository holds its own,
under the prefix its `module.yml` names (`requirements: { prefix: GW, parent: robohub }`).

## Identifiers

`SYS-0001` for the system; a prefix per repository for the rest — `GW`
(gateway), `KEEP` (keeper), `MESH`, `PICO`, `AQUA`, `ENER`, … — and a
sub-prefix per subsystem where a repository has them (`KEEP-AUTH-0003`). An
identifier is never reused: a requirement that is dropped is `retired`, not
deleted. ADRs are numbered per repository (`ADR-0009`) and named from another
repository as `robohub-gateway:ADR-0009`.

## A requirement's life

```
draft → proposed → approved → implemented → verified
                 ↘ rejected        any → retired
```

- **draft** — being written; nobody relies on it.
- **proposed** — ready to be decided. Anyone may propose.
- **approved** — the maintainer has accepted it. Work may start.
- **implemented** — the code carries its `@req` tag.
- **verified** — a test tagged `@verifies` passes, and kept passing.
- **rejected** / **retired** — kept for the record, with the reason.

Changing what an approved requirement *says* sends it back to `proposed`: it is
a different requirement until it is approved again. Only the maintainer
approves a requirement or accepts an ADR (see *Who decides*).

## How a feature is made

1. **Requirement.** Write it at the level it belongs to, as `proposed`, with
   what it serves. If it needs requirements in other repositories, write those
   too, each serving this one.
2. **Decision.** If it changes how the system is built — a new interface, a new
   protocol field, a new dependency, a choice between two designs — write an
   ADR, `proposed`, linked to the requirement. A change inside one module that
   no one else sees needs none.
3. **Approval.** The maintainer approves the requirements and accepts the ADR.
4. **Implementation.** Tag the code that meets it: `// @req GW-0012`.
5. **Tests.** Tag what proves it: `// @verifies GW-0012` above the `test fn`,
   C test or smoke script.
6. **Check.** `rho req check` in every pull request; `rho req trace` shows the
   matrix and its gaps. A requirement is marked `verified` when its tests pass.
7. **Release.** A release is made only when every approved requirement it
   contains is verified (`rho req trace --release`).

A bug fix follows the same path in small: the requirement it breaks is found
(or written, when the bug shows one was missing), and the test that would have
caught it is tagged with it.

## The tools

| Command | Does |
|---|---|
| `rho req check` | Validates the files and every link; refuses an approval not made by the maintainer |
| `rho req trace` | The trace matrix, with the last test results and every gap |
| `rho req render` | The requirements as Markdown, on demand — not committed; the documentation site shows the same |
| `rho req new`, `edit`, `set-status` | Edit the files without disturbing the rest of them |
| `rho req adr new`, `list`, `supersede` | Number, write and replace ADRs |

`--workspace` runs any of them over every repository checked out beside this
one, so a SYS requirement is traced through all the repositories that serve it.

The keeper's **Developer** section shows the same: requirements to browse and
edit, ADRs, the trace matrix and the Markdown export. It edits your working copy
and can commit to a branch; it never pushes.

## Who decides

The repositories are public, and anyone may propose a change by pull request —
a requirement, an ADR, code. Only the maintainer, named in
`robohub/MAINTAINERS.yml`, approves requirements, accepts ADRs and merges to
`main`.

What makes that hold is GitHub's: `main` is protected, so changes arrive only by
pull request with the checks green, and `CODEOWNERS` requires the maintainer's
review for `docs/requirements/`, `docs/architecture/` and `module.yml`. `rho req
check` adds a guard on top — a pull request that sets a requirement to
`approved` is refused unless its commits are the maintainer's — but a commit's
author can be written by anyone, so the guard is a seatbelt and the protected
branch is the lock.

How the protection is switched on, and what it means day to day, is in
{ref}`robohub/process/governance`.
