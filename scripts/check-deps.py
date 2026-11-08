#!/usr/bin/env python3
"""Check that every RoboHub module, plugin and module instance is declared.

A module or plugin is used when a Rho source includes its main file, when an
application lists it under `modules:`, or when it lists a plugin under
`plugins:`. All of those have to name it under `deps.robohub`; a RoboHub
dependency at the top level, beside the Rho components, is refused. The
version lives in `deps.robohub` only, not again in the `modules:` entry.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = sorted(
    p for base in ("applications", "modules", "plugins")
    for p in (ROOT / base).glob("*/module.yml")
    if "tests" not in p.parts
)

known = {}
for base in ("modules", "plugins"):
    for path in (ROOT / base).glob("*/module.yml"):
        data = yaml.safe_load(path.read_text()) or {}
        name = (data.get("module") or data.get("application") or {}).get("name") or path.parent.name
        known[name] = base

errors = []


def module_name(data, path):
    return (data.get("module") or data.get("application") or {}).get("name") or path.parent.name


def included_modules(module_dir, self_name):
    used = set()
    for source in module_dir.rglob("*.rho"):
        text = source.read_text(errors="replace")
        for match in re.finditer(r'^\s*include\s+"([^"]+)"', text, re.M):
            include = match.group(1)
            candidates = [
                (source.parent / include).resolve(),
                (module_dir / include).resolve(),
                (ROOT / include).resolve(),
            ]
            for candidate in candidates:
                try:
                    rel = candidate.relative_to(ROOT)
                except ValueError:
                    continue
                parts = rel.parts
                if (len(parts) >= 4 and parts[0] in ("modules", "plugins") and
                        parts[2] == "src" and parts[-1] == "main.rho" and parts[1] != self_name):
                    used.add(parts[1])
                    break
    return used


for manifest in MANIFESTS:
    data = yaml.safe_load(manifest.read_text()) or {}
    name = module_name(data, manifest)
    deps = data.get("deps") or {}
    robohub = deps.get("robohub") or {}
    flat = [key for key in deps if key != "robohub"]

    def require(used, where):
        for item in sorted(used):
            if item not in robohub:
                errors.append(f"{manifest}: {where} uses {item!r}, but it is not under deps.robohub")

    require(included_modules(manifest.parent, name), "source")
    require({entry.get("name") for entry in data.get("modules") or [] if isinstance(entry, dict)}, "modules")
    require({entry.get("name") for entry in data.get("plugins") or [] if isinstance(entry, dict)}, "plugins")

    for item in flat:
        if item in known:
            errors.append(f"{manifest}: RoboHub dependency {item!r} is at the top level; move it under deps.robohub")
    for entry in data.get("modules") or []:
        if isinstance(entry, dict) and "version" in entry:
            errors.append(f"{manifest}: modules entry {entry.get('name')!r} repeats version; keep it in deps.robohub")
    for entry in data.get("plugins") or []:
        if isinstance(entry, dict) and "version" in entry:
            errors.append(f"{manifest}: plugins entry {entry.get('name')!r} repeats version; keep it in deps.robohub")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    sys.exit(1)
print("dependencies are declared for every application, module and plugin")
