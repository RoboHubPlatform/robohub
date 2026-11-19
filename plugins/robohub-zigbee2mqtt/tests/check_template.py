#!/usr/bin/env python3
"""
check_template.py — the configuration template carries no secret and leaves
nothing open (Z2MP-0003).

The template is published with the plugin, and Mesh writes it into every
coordinator's data directory with the placeholders filled. So it is checked as
text, before any placeholder is filled — which is also why it is read with a
small reader here and not a YAML library: `adapter: {adapter}` is not the YAML
it becomes until Mesh has filled it.

  - mqtt.password and advanced.network_key are only `!secret` references, and
    nothing else in the template looks like a password, key or token;
  - advanced.pan_id and ext_pan_id are GENERATE;
  - availability is enabled, the frontend and Home Assistant are disabled;
  - every placeholder Mesh fills is there, and no other;
  - `version` is the configuration version Zigbee2MQTT 2.14.3 writes (5), and the
    manifest's zigbee2mqtt block names this template and that version.

Prints a [PASS]/[FAIL] line per check and exits non-zero on any failure.

@project RoboHub Platform
@license MIT
"""

import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(PLUGIN, "templates", "configuration.yaml")
MANIFEST = os.path.join(PLUGIN, "module.yml")

# What Mesh fills, each where it belongs.
PLACEHOLDERS = {
    "{coordinator}", "{mesh}", "{server}", "{user}", "{base_topic}",
    "{serial_port}", "{adapter}", "{channel}",
}
# The configuration-file version Zigbee2MQTT 2.14.3 expects: CURRENT_VERSION in
# lib/util/settings.ts at the 2.14.3 tag.
CONFIG_VERSION = "5"


def uncomment(line):
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def values(text):
    """Every `a.b: value` of a two-level document, comments taken off."""
    out = {}
    parent = ""
    for raw in text.splitlines():
        line = uncomment(raw)
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if not line.startswith(" "):
            parent = key.strip()
            if value:
                out[parent] = value
            continue
        out[parent + "." + key.strip()] = value
    return out


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


# @verifies Z2MP-0003
def problems_of(text):
    """What is wrong with a template, as sentences; [] when nothing is."""
    found = []
    v = values(text)
    body = "\n".join(uncomment(line) for line in text.splitlines())

    for key, ref in (("mqtt.password", "!secret password"), ("advanced.network_key", "!secret network_key")):
        if unquote(v.get(key, "")) != ref:
            found.append("%s is not the reference '%s'" % (key, ref))
    for key, value in v.items():
        leaf = key.rsplit(".", 1)[-1]
        if re.search(r"password|secret|token|key", leaf) and key not in ("mqtt.password", "advanced.network_key"):
            found.append("%s may carry a secret" % key)
        if unquote(value).startswith("!") and key not in ("mqtt.password", "advanced.network_key"):
            found.append("%s is a reference the template does not expect" % key)
    if re.search(r"network_key:\s*\[", body):
        found.append("a network key is written out")

    for key in ("advanced.pan_id", "advanced.ext_pan_id"):
        if unquote(v.get(key, "")) != "GENERATE":
            found.append("%s is not GENERATE" % key)
    for key, want in (("availability.enabled", "true"), ("frontend.enabled", "false"),
                      ("homeassistant.enabled", "false")):
        if v.get(key) != want:
            found.append("%s is not %s" % (key, want))

    used = set(re.findall(r"\{[a-z_]+\}", text))
    for missing in sorted(PLACEHOLDERS - used):
        found.append("the placeholder %s is not in the template" % missing)
    for extra in sorted(used - PLACEHOLDERS):
        found.append("%s is a placeholder Mesh does not fill" % extra)
    for key, want in (("mqtt.server", "{server}"), ("mqtt.user", "{user}"),
                      ("mqtt.base_topic", "{base_topic}"), ("mqtt.client_id", "{user}"),
                      ("serial.port", "{serial_port}"), ("serial.adapter", "{adapter}"),
                      ("advanced.channel", "{channel}")):
        if unquote(v.get(key, "")) != want:
            found.append("%s is not %s" % (key, want))

    if v.get("version") != CONFIG_VERSION:
        found.append("version is not %s, the configuration version Zigbee2MQTT 2.14.3 writes" % CONFIG_VERSION)
    return found


def main():
    failures = 0

    def check(ok, what):
        nonlocal failures
        print("[PASS] %s" % what if ok else "[FAIL] %s" % what)
        if not ok:
            failures += 1

    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    found = problems_of(template)
    for problem in found:
        print("  templates/configuration.yaml: %s" % problem)
    check(found == [], "the template carries no secret, generates its network identity and leaves nothing open")

    # The check itself catches what it is for.
    broken = [
        ("a password written out", template.replace('"!secret password"', '"hunter2"')),
        ("a network key written out", template.replace('"!secret network_key"', "[1, 3, 5, 7, 9, 11, 13, 15, 0, 2, 4, 6, 8, 10, 12, 13]")),
        ("a fixed PAN id", template.replace("pan_id: GENERATE\n  ext", "pan_id: 6754\n  ext")),
        ("a fixed extended PAN id", template.replace("ext_pan_id: GENERATE", "ext_pan_id: [221, 221, 221, 221, 221, 221, 221, 221]")),
        ("the frontend on", template.replace("frontend:\n  enabled: false", "frontend:\n  enabled: true")),
        ("Home Assistant on", template.replace("homeassistant:\n  enabled: false", "homeassistant:\n  enabled: true")),
        ("availability off", template.replace("availability:\n  enabled: true", "availability:\n  enabled: false")),
        ("a placeholder missing", template.replace('"{serial_port}"', '"/dev/ttyUSB0"')),
        ("an auth token", template.replace("frontend:\n  enabled: false", "frontend:\n  enabled: false\n  auth_token: abc")),
        ("the old version", template.replace("version: 5", "version: 4")),
    ]
    for what, text in broken:
        check(text != template and problems_of(text) != [], "the check refuses a template with %s" % what)

    with open(MANIFEST, encoding="utf-8") as f:
        manifest = values(f.read())
    check(unquote(manifest.get("zigbee2mqtt.config", "")) == "templates/configuration.yaml",
          "the manifest's zigbee2mqtt.config names this template")
    check(unquote(manifest.get("zigbee2mqtt.version", "")) == "2.14.3" and
          unquote(manifest.get("zigbee2mqtt.image", "")).endswith(":2.14.3") and
          "/2.14.3.tar.gz" in manifest.get("zigbee2mqtt.source", ""),
          "the version, the source and the image are the one pinned version, 2.14.3")

    if failures:
        print("%d check(s) failed" % failures)
        return 1
    print("the configuration template is safe to publish")
    return 0


if __name__ == "__main__":
    sys.exit(main())
