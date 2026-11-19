#!/usr/bin/env python3
"""The widgets stream: only for a signed-in person, and only this application's.

`GET /widgets/events` follows the application's own widget events. Without a
session it is not opened; with a ticket for another application it is not
opened; and what it sends comes from this application's workspace only — a feed
another application (or a program started without a workspace) keeps under
~/.rho is never read.
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import aquarium_host  # noqa: E402
import csrf_probe  # noqa: E402


def open_stream(host, headers):
    request = urllib.request.Request(host.base + "/widgets/events")
    for name, value in headers.items():
        request.add_header(name, value)
    opener = urllib.request.build_opener(aquarium_host._NoRedirect)
    try:
        return opener.open(request, timeout=5), None
    except urllib.error.HTTPError as error:
        return None, error.code


def ticket_for(host, audience):
    keys = os.path.join(host.home, ".rho", "auth")
    return subprocess.run(
        [aquarium_host.RHO, "auth", "ticket", "--private", os.path.join(keys, "private.pem"),
         "--issuer", "keeper", "--audience", audience, "--subject", "smoke",
         "--scopes", "*", "--ttl", "1h"], check=True, capture_output=True, text=True).stdout.strip()


# @verifies WIDG-0008, WIDG-0015
def main() -> int:
    with aquarium_host.running() as host:
        # A feed kept elsewhere: another application's, and the one a program
        # started without a workspace would use.
        for app in ("energy", "aquarium"):
            elsewhere = Path(host.home) / ".rho" / "apps" / app / "data"
            elsewhere.mkdir(parents=True, exist_ok=True)
            (elsewhere / "events.jsonl").write_text(
                'event: widget-cards-en\ndata: {"decoy":"OTHER-APP-SECRET"}\n\n')
        csrf = host.get("/widgets").split('name="csrf" value="', 1)[1].split('"', 1)[0]
        csrf_probe.post(host.base, "/widgets/add", {"title": "Own widget", "kind": "numeric",
                                                    "source_kind": "manual", "csrf": csrf},
                        bearer=host.token)

        for label, headers in (("no session", {"Accept": "text/event-stream"}),
                               ("a ticket for energy", {"Authorization": "Bearer " + ticket_for(host, "energy")}),
                               ("a forged session cookie", {"Cookie": "rho_session_aquarium=forged"})):
            stream, status = open_stream(host, headers)
            if stream is not None:
                stream.close()
                raise AssertionError(f"the stream opened with {label}")
            if status not in (302, 401, 403):
                raise AssertionError(f"the stream with {label} was answered {status}")

        stream, status = open_stream(host, {"Authorization": "Bearer " + host.token})
        if stream is None:
            raise AssertionError(f"the stream did not open for a signed-in person ({status})")
        try:
            if not stream.headers.get("Content-Type", "").startswith("text/event-stream"):
                raise AssertionError(f"the stream is {stream.headers.get('Content-Type')}")
            received = b""
            deadline = time.time() + 6
            while time.time() < deadline and b"Own widget" not in received:
                try:
                    received += stream.read1(65536)
                except (TimeoutError, OSError):
                    break
        finally:
            stream.close()
        text = received.decode("utf-8", "replace")
        if "Own widget" not in text:
            raise AssertionError(f"the stream did not carry this application's widget: {text[:200]!r}")
        if "OTHER-APP-SECRET" in text:
            raise AssertionError("the stream carried a feed from outside the application's workspace")
    return 0


if __name__ == "__main__":
    sys.exit(main())
