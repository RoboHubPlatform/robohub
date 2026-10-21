# RoboHub Orchestrator

The orchestrator of the RoboHub ecosystem: a registry of its modules, and the
tools that run over all of them.

The ecosystem is a set of repositories — the interfaces every platform
implements, a platform per family of parts, the runtime and transport the nodes
speak, the devices and drivers they are made of, and the gateway that collects
them. Each is versioned apart and built apart, which is right for the code and
wrong for the questions a person asks about the whole: which modules are there,
which version of each, and does any of it still build.

Those questions are about the ecosystem rather than about a repository, and this
is where they are answered.

## The registry

Every module of the ecosystem is described in `registry/modules/`, one file per
module:

```yaml
name: robohub-avr
role: platform
path: ../robohub-avr
git: https://github.com/RoboHubPlatform/robohub-avr
summary: The 8-bit AVR platform: the interfaces on an ATmega328P, and the Arduino UNO R3.
```

The registry says where a module is and what it is for in the ecosystem. The
module's own manifest is the truth about what it *is*, and the registry does
not repeat it: a registry that repeats what a module already says is a second
copy that drifts.

```sh
robohub registry list          # every module
robohub registry show avr      # one module, in full
robohub registry check         # whether the ecosystem is whole
```

## The registry of tests

Every module keeps a registry of its tests: what they are called, which kind
they are, whether they are run, and the command that runs them. The tests
themselves are in folders — the unit tests in one, the smoke tests in another,
and as many more of either as the project finds useful — and each folder keeps a
registry of its own, so that no registry grows past what it can be read as. The
module's own registry says which registries there are.

```yaml
# tests/registry.yml
name: robohub-avr
registries:
  unit: unit/registry.yml
  smoke: smoke/registry.yml
```

```yaml
# tests/unit/registry.yml
tests:
  the platform's own tests:
    state: enabled
    program: "sh"
    arguments: "tests/unit/run.sh"
```

A test that is not enabled is still a test: it is there, and it is not run. A
run of "all" is the tests that are enabled, and a run of one kind is the tests
of that kind that are enabled.

`robohub test add` registers a test that has been written — and runs it first.
A registry that holds a test which does not work is a registry that will fail a
run for a reason nobody can see, so a test is added only after it has passed.

## The schemas

The shapes the ecosystem's files are written in are in `schemas/`, one file per
shape and one version per file: `board.v1.json`, `target-spec.v1.json`,
`registry.v1.json` and `suite.v1.json`. They are JSON Schema, so anything else
can check against them too.

The rules themselves are written in Rho, in `src/validate.rho`, so that a
program can keep them. The two are the same contract: what a rule says in one is
what a schema says in the other.

The manifests are the toolchain's own business — `rho module validate` is the
authority on what a manifest may say, and it is what the toolchain reads. What
the orchestrator checks is the ecosystem's own files.

## The tools

The tools are the toolchain's own components, run over each module in turn.
The orchestrator decides *what* to run them over and collects what they said;
the components decide how to run and what their findings mean. A second linter
here would be a linter that reports something else.

```sh
robohub lint                   # static analysis, over every module
robohub lint robohub-avr       # over one
robohub test                   # the tests, over every module
robohub test robohub-avr       # over one
robohub test robohub-avr --unit    # only the unit tests
robohub test robohub-avr --smoke   # only the smoke tests
robohub test list robohub-avr     # what tests the module has
robohub test run robohub-avr NAME # one of them, by its name
robohub test enable robohub-avr NAME   # a test is run
robohub test disable robohub-avr NAME  # a test is not run
robohub docs                   # documentation
```

Each run writes what the tool said to `build/reports/<tool>-<module>.txt`, so
a report survives the run that produced it.

## Running it

The orchestrator is a Rho program, generated as a Go target by the toolchain:

```sh
rho build .            # build/generated/go, and build/robohub
./build/robohub registry list
```

Its tests are run by the toolchain's own runner:

```sh
rho test .
```

## What is shared

The material every repository in the ecosystem needs and none of them should
own is here: the ignore rules, the configuration a CI build resolves, and the
workflow itself. See `shared/`.
