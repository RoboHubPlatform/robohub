#!/usr/bin/env python3
"""The theme switch returns to a page on this origin, and nowhere else.

`GET /ui/theme?set=…&back=…` keeps the theme in a cookie and sends the browser
back to `back`. A `back` that names another site — directly, through a backslash
or a tab a browser drops, or by a line break that starts a header of its own —
is answered with `/`, and the person's menu draws `back` as one escaped value.
"""

import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import aquarium_host  # noqa: E402

FOREIGN = [
    "//evil.example", "https://evil.example", "/\\evil.example", "\\\\evil.example",
    "/\t/evil.example", "/\n/evil.example", "/\r\nSet-Cookie: stolen=1", "/ok\x0bx",
    "/\x00", "/\x7f", 'evil.example', '/"><script>alert(1)</script>', "",
]


# @verifies UI-0002, UI-0006
def main() -> int:
    with aquarium_host.running() as host:
        for back in FOREIGN:
            query = urllib.parse.urlencode({"set": "light", "back": back})
            status, headers, _ = host.request("/ui/theme?" + query, follow=False)
            location = headers.get("Location", "")
            if status != 302 or location != "/":
                raise AssertionError(f"back={back!r} was answered {status} to {location!r}")
            cookies = headers.get_all("Set-Cookie") or []
            if len(cookies) != 1 or not cookies[0].startswith("rho_theme=light") and "theme=light" not in cookies[0]:
                raise AssertionError(f"back={back!r} set {cookies}")
        # A page on this origin, with its query, is where it returns.
        query = urllib.parse.urlencode({"set": "system", "back": "/expenses?tab=items&x=1"})
        status, headers, _ = host.request("/ui/theme?" + query, follow=False)
        if status != 302 or headers.get("Location") != "/expenses?tab=items&x=1":
            raise AssertionError(f"a local page was answered {status} to {headers.get('Location')!r}")
        # A theme that is not one of the three is the default, never text in a cookie.
        status, headers, _ = host.request("/ui/theme?set=" + urllib.parse.quote("dark; Domain=evil.example") + "&back=/",
                                          follow=False)
        if "evil.example" in " ".join(headers.get_all("Set-Cookie") or []):
            raise AssertionError("a theme value reached the cookie")
    return 0


if __name__ == "__main__":
    sys.exit(main())
