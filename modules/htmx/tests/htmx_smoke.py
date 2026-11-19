#!/usr/bin/env python3
"""The asset route serves the two scripts it carries, and nothing else.

`GET /assets/{file}` answers htmx.min.js and sse.min.js as JavaScript that is
not sniffed as anything else. Any other name — the licences beside them, the
module's own files, a path that climbs out of the folder in any spelling — is
404 and carries nothing of the file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import aquarium_host  # noqa: E402

REFUSED = [
    "LICENSE-htmx", "LICENSE-sse", "htmx.js", "HTMX.MIN.JS", "htmx.min.js.map",
    "..%2fmodule.yml", "..%2F..%2Fmodule.yml", "%2e%2e%2fsrc%2fhtmx.rho",
    "..%5cmodule.yml", "htmx.min.js%00.txt", "htmx.min.js%2f..%2fLICENSE-htmx",
    "%2fetc%2fpasswd", "assets%2fhtmx.min.js", "sse.min.js%20",
]


# @verifies HTMX-0002
def main() -> int:
    with aquarium_host.running() as host:
        for name in ("htmx.min.js", "sse.min.js"):
            # The scripts are served before sign-in: the login page needs them.
            status, headers, body = host.request("/assets/" + name, bearer=False)
            if status != 200 or not headers.get("Content-Type", "").startswith("text/javascript"):
                raise AssertionError(f"{name} was answered {status} {headers.get('Content-Type')}")
            if headers.get("X-Content-Type-Options") != "nosniff" or len(body) < 1000:
                raise AssertionError(f"{name} is not the script, or may be sniffed")
        for name in REFUSED:
            status, _, body = host.request("/assets/" + name, bearer=False)
            if status not in (404, 400, 301, 302, 307, 308) or "Permission is hereby granted" in body \
                    or "module:" in body or "root:" in body:
                raise AssertionError(f"/assets/{name} was answered {status}: {body[:80]!r}")
            if status == 200:
                raise AssertionError(f"/assets/{name} was served")
    return 0


if __name__ == "__main__":
    sys.exit(main())
