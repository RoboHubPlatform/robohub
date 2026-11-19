#!/usr/bin/env python3
"""The language switch returns to a page on this origin, and its pages escape it.

`POST /i18n/locale` keeps the language in a cookie and sends the browser back to
`next`. A `next` that names another site — directly, through a backslash or a
tab a browser drops — or holds a line break that would start a header is
answered with `/`. A language that is not offered is English, never text in the
cookie. The switcher every page draws holds the page's own path as one escaped
value.
"""

import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import aquarium_host  # noqa: E402

FOREIGN = [
    "//evil.example", "https://evil.example", "/\\evil.example", "/\t/evil.example",
    "/\n/evil.example", "/ok\r\nX-Evil: 1", "/ok\x0cx", "/\x00", "/\x7f", "evil.example",
    "javascript:alert(1)", '/"><script>alert(1)</script>', "",
]


# @verifies I18N-0002, I18N-0003
def main() -> int:
    with aquarium_host.running() as host:
        for wanted in FOREIGN:
            request_status, headers = post_headers(host, {"locale": "ro", "next": wanted})
            location = headers.get("Location", "")
            if request_status != 302 or location != "/" or headers.get("HX-Redirect") != "/":
                raise AssertionError(f"next={wanted!r} returned to {location!r} ({request_status})")
            if headers.get("X-Evil"):
                raise AssertionError(f"next={wanted!r} wrote a header")
        status, headers = post_headers(host, {"locale": "ro", "next": "/expenses?tab=items"})
        if headers.get("Location") != "/expenses?tab=items":
            raise AssertionError(f"a local page was answered {headers.get('Location')!r}")
        status, headers = post_headers(host, {"locale": "ro; Domain=evil.example", "next": "/"})
        cookie = " ".join(headers.get_all("Set-Cookie") or [])
        if "evil.example" in cookie or "locale=en" not in cookie:
            raise AssertionError(f"an unknown language reached the cookie: {cookie!r}")
        # The switcher draws the page's path escaped, whatever the path holds.
        page = host.get("/widgets?x=" + urllib.parse.quote('"><script>alert(1)</script>'))
        if "<script>alert(1)" in page or 'name="next" value="/widgets"' not in page:
            raise AssertionError("the switcher does not hold the page's path, escaped")
    return 0


def post_headers(host, fields):
    import urllib.request
    import urllib.error
    request = urllib.request.Request(host.base + "/i18n/locale",
                                     data=urllib.parse.urlencode(fields).encode(), method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    opener = urllib.request.build_opener(aquarium_host._NoRedirect)
    try:
        with opener.open(request, timeout=10) as response:
            return response.status, response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.headers


if __name__ == "__main__":
    sys.exit(main())
