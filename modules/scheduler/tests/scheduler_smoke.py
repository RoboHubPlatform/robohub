#!/usr/bin/env python3
"""Smoke test for the scheduler module inside the aquarium host.

Creates an interval chore, completes it, snoozes it, and drives a usage-based
chore to due. The database path is checked as well: modules share the host's
main SQL database under the application workspace.
"""

import html
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import csrf_probe  # noqa: E402

HERE = Path(__file__).resolve()
MODULE = HERE.parents[1]
ROBOHUB = MODULE.parents[1]
PROJECTS = ROBOHUB.parent
# The host the module is tested in: the aquarium, in its own repository beside
# this one, or where ROBOHUB_AQUARIUM says.
HOST = Path(os.environ.get("ROBOHUB_AQUARIUM", str(PROJECTS / "robohub-aquarium")))
RHO = PROJECTS / "rho" / "bin" / "rho"

# The bearer ticket every request carries: one the keeper would issue for the
# host, minted by the test with a key pair of its own (see mint_token).
TOKEN = ""


def mint_token(home: str, audience: str) -> str:
    """A ticket for the host, as the keeper would issue one.

    The host verifies tickets against ~/.rho/auth/public.pem in its own home,
    so the test makes a key pair there and signs the ticket with it.
    """
    rho = str(RHO) if RHO.exists() else "rho"
    keys = os.path.join(home, ".rho", "auth")
    os.makedirs(keys, exist_ok=True)
    subprocess.run([rho, "auth", "keygen", "--dir", keys, "--force"],
                   check=True, capture_output=True, text=True)
    result = subprocess.run(
        [rho, "auth", "ticket", "--private", os.path.join(keys, "private.pem"),
         "--issuer", "keeper", "--audience", audience, "--subject", "smoke",
         "--scopes", "*", "--ttl", "1h"],
        check=True, capture_output=True, text=True)
    return result.stdout.strip()


CSRF = ""


def learn_csrf(base: str, page: str) -> None:
    """The form token the host draws its forms with, which every post carries."""
    global CSRF
    with open_url(base + page) as response:
        text = response.read().decode("utf-8", "replace")
    found = re.search(r'name="csrf" value="([^"]*)"', text)
    if not found:
        raise AssertionError(f"{page} draws no form token")
    CSRF = html.unescape(found.group(1))


def open_url(target, timeout: float = 10):
    """urlopen with the test's ticket, which every page of the host asks for."""
    request = target if isinstance(target, urllib.request.Request) else urllib.request.Request(target)
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    return urllib.request.urlopen(request, timeout=timeout)



def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(base: str) -> None:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            with open_url(base + "/scheduler", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    raise SystemExit(f"aquarium did not start at {base}")


def get(base: str, path: str) -> str:
    with open_url(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post(base: str, path: str, fields: dict) -> dict:
    if CSRF and "csrf" not in fields:
        fields = dict(fields, csrf=CSRF)
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with open_url(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def assert_contains(haystack: str, needles: list, label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} does not contain {needle!r}")


def build() -> Path:
    binary = HOST / "build" / "aquarium"
    rho = str(RHO) if RHO.exists() else "rho"
    result = subprocess.run([rho, "build", str(HOST)], cwd=ROBOHUB, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise SystemExit("aquarium build failed:\n" + result.stdout + result.stderr)
    if not binary.exists():
        raise SystemExit(f"aquarium build wrote no binary at {binary}")
    return binary


def main() -> int:
    binary = build()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    # The workspace's path holds a space, as a person's home or a folder they
    # chose may: every directory the modules make is made there, whole, and
    # nothing is made from the path's first word (/tmp/scheduler) or its second
    # (smoke-…, relative to where the application runs).
    tmp_first_word = Path(tempfile.gettempdir()) / "scheduler"
    had_first_word = tmp_first_word.exists()
    with tempfile.TemporaryDirectory(prefix="scheduler smoke-") as workspace:
        second_word = HOST / Path(workspace).name.split(" ", 1)[1]
        env = dict(os.environ)
        # The application finds the toolchain (the documentation generator, the
        # components) by its home; the test gives the application a HOME of its own,
        # so the toolchain's home is named before that happens.
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        env["XDG_STATE_HOME"] = os.path.join(workspace, "state")
        global TOKEN
        auth_home = env.get("HOME") if env.get("HOME", "").startswith(tempfile.gettempdir()) else tempfile.mkdtemp(prefix="aquarium-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        def start():
            return subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    text=True)

        def stop(proc):
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

        process = start()
        try:
            wait_for(base)
            # @verifies SCHED-0011, SET-0001, LOG-0002
            if not (Path(workspace) / "data" / "settings.conf").parent.is_dir():
                raise AssertionError("the data directory is not under the workspace whose path holds a space")
            if not (Path(workspace) / "state" / "robohub" / "aquarium").is_dir():
                raise AssertionError("the log directory is not under a state directory whose path holds a space")
            if second_word.exists() or (tmp_first_word.exists() and not had_first_word):
                raise AssertionError(f"a directory was made from a word of the workspace's path: {second_word} or {tmp_first_word}")
            learn_csrf(base, "/scheduler")
            page = get(base, "/scheduler")
            # The host may seed chores of its own; the test's are found by title.
            assert_contains(page, ["Maintenance schedule", "Add a chore"], "the scheduler")

            assert post(base, "/api/scheduler/chores", {
                "title": "Change filter sock",
                "kind": "interval",
                "interval_hours": "72",
                "grace_hours": "12",
                "priority": "high",
            })["ok"]
            chores = {c["title"]: c for c in json.loads(get(base, "/api/scheduler/chores"))}
            sock = chores.get("Change filter sock")
            if not sock or sock["status"] != "pending":
                raise AssertionError(f"unexpected chores: {chores}")
            sock_id = sock["id"]

            assert post(base, f"/api/scheduler/chores/{sock_id}/complete", {"note": "Cleaned"})["ok"]
            completed = get(base, "/scheduler")
            assert_contains(completed, ["Cleaned", "Change filter sock"], "completion log")

            assert post(base, f"/api/scheduler/chores/{sock_id}/snooze", {"hours": "24"})["ok"]

            assert post(base, "/api/scheduler/chores", {
                "title": "UV bulb",
                "kind": "usage",
                "usage_hours": "4000",
                "priority": "critical",
            })["ok"]
            uv_id = {c["title"]: c for c in json.loads(get(base, "/api/scheduler/chores"))}["UV bulb"]["id"]
            assert post(base, f"/api/scheduler/chores/{uv_id}/usage", {"hours": "4000"})["ok"]
            chores = json.loads(get(base, "/api/scheduler/chores"))
            uv = [chore for chore in chores if chore["title"] == "UV bulb"][0]
            if uv["status"] != "due":
                raise AssertionError(f"usage chore should be due: {uv}")

            # The API is for code: a bearer ticket (or the form token) is needed,
            # and a post that rides only on the browser's cookie is refused.
            # @verifies SCHED-0013
            cookie = csrf_probe.cookie_session(csrf_probe.rho_binary(PROJECTS), auth_home, base, "aquarium")
            before = csrf_probe.workspace_state(workspace)
            for path, fields in (("/api/scheduler/chores", {"title": "Forged", "kind": "interval", "interval_hours": "1"}),
                                 (f"/api/scheduler/chores/{sock_id}/complete", {"note": "Forged"}),
                                 (f"/api/scheduler/chores/{sock_id}/snooze", {"hours": "999"}),
                                 (f"/api/scheduler/chores/{uv_id}/usage", {"hours": "1"})):
                for label, extra in (("no token", {}), ("a wrong token", {"csrf": "c" * 64})):
                    status, _ = csrf_probe.post(base, path, dict(fields, **extra), cookie=cookie)
                    if status != 403:
                        raise AssertionError(f"{path} with only a cookie and {label} was answered {status}")
            changed = csrf_probe.state_diff(before, csrf_probe.workspace_state(workspace))
            if changed:
                raise AssertionError(f"a refused API post changed {changed}")
            status, _ = csrf_probe.post(base, f"/api/scheduler/chores/{uv_id}/usage",
                                        {"hours": "1", "csrf": CSRF}, cookie=cookie)
            if status != 200:
                raise AssertionError(f"the API with the form token was answered {status}")

            db = Path(workspace) / "data" / "app.db"
            if not db.exists():
                raise AssertionError("the scheduler records are not in the host's main database")

            # An action on a chore that is not there, or that cannot be done, is
            # answered as the failure it is, never `ok`.
            # @verifies SCHED-0015
            def api_post(path, fields):
                request = urllib.request.Request(base + path, method="POST",
                    data=urllib.parse.urlencode(fields).encode())
                request.add_header("Content-Type", "application/x-www-form-urlencoded")
                try:
                    with open_url(request, timeout=20) as response:
                        return response.status, json.loads(response.read().decode())
                except urllib.error.HTTPError as error:
                    return error.code, json.loads(error.read().decode())
            for path, fields, wanted in (("/api/scheduler/chores/987654/complete", {"note": "x"}, 404),
                                         ("/api/scheduler/chores/987654/snooze", {"hours": "1"}, 404),
                                         ("/api/scheduler/chores/987654/usage", {"hours": "1"}, 404),
                                         (f"/api/scheduler/chores/{uv_id}/usage", {"hours": "0"}, 400)):
                status, answer = api_post(path, fields)
                if status != wanted or answer.get("ok") is not False or not answer.get("error"):
                    raise AssertionError(f"{path} {fields} was answered {status} {answer}, wanted {wanted} and the reason")

            # More chores than one page of 256: every one is listed, on the page
            # and by the API, and the last one can be acted on.
            # @verifies SCHED-0014
            import sqlite3
            far = 4000000000
            with sqlite3.connect(db) as conn:
                conn.executemany("INSERT INTO chores (title, schedule_kind, interval_hours, next_due_epoch) VALUES (?, 'interval', 24, ?)",
                                 [(f"Bulk chore {i:03d}", far + i) for i in range(300)])
            listed = json.loads(get(base, "/api/scheduler/chores"))
            bulk = [c for c in listed if c["title"].startswith("Bulk chore ")]
            if len(bulk) != 300 or len({c["id"] for c in listed}) != len(listed):
                raise AssertionError(f"the API listed {len(bulk)} of 300 bulk chores ({len(listed)} in all, ids unique: {len({c['id'] for c in listed}) == len(listed)})")
            last = [c for c in bulk if c["title"] == "Bulk chore 299"][0]
            status, answer = api_post(f"/api/scheduler/chores/{last['id']}/complete", {"note": "the 300th"})
            if status != 200 or not answer.get("ok"):
                raise AssertionError(f"the last chore past 256 could not be completed: {status} {answer}")
            assert_contains(get(base, "/scheduler"), ["Bulk chore 000", "Bulk chore 299", "the 300th"], "the page past 256 chores")
            assert_contains(get(base, f"/scheduler/chores/edit?id={last['id']}"), ["Bulk chore 299"], "the edit page of a chore past 256")
            with sqlite3.connect(db) as conn:
                conn.execute("DELETE FROM chores WHERE title LIKE 'Bulk chore %'")

            # A chore that uses an inventory item takes it off the shelf when it
            # is done, and says so on its row.
            get(base, "/expenses")
            with sqlite3.connect(db) as conn:
                conn.execute("INSERT INTO items (name, unit, quantity_milli, kind, handle) VALUES ('Filter pads', 'pcs', 3000, 'part', 'filter-pads')")
            assert post(base, "/api/scheduler/chores", {
                "title": "Rinse filter",
                "kind": "interval",
                "interval_hours": "720",
                "runtime_of": "Filter Main",
                "consumes": "filter-pads",
                "consumes_qty": "1",
            })["ok"]
            with sqlite3.connect(db) as conn:
                chore_id, runtime_of, consumes, milli = conn.execute(
                    "SELECT id, runtime_of, consumes, consumes_milli FROM chores WHERE title='Rinse filter'").fetchone()
            if (runtime_of, consumes, milli) != ("filter-main", "filter-pads", 1000):
                raise AssertionError(f"the chore's links: {runtime_of!r} {consumes!r} {milli}")
            assert_contains(get(base, "/scheduler"), ["runtime of filter-main", "uses 1 × filter-pads"], "the chore's row")
            assert post(base, f"/api/scheduler/chores/{chore_id}/complete", {"note": "Rinsed"})["ok"]
            with sqlite3.connect(db) as conn:
                left = conn.execute("SELECT quantity_milli FROM items WHERE handle='filter-pads'").fetchone()[0]
                moved = conn.execute("SELECT kind, quantity_milli, source FROM stock_movements WHERE item_id = (SELECT id FROM items WHERE handle='filter-pads')").fetchall()
            if left != 2000 or moved != [("consume", -1000, f"chore#{chore_id}")]:
                raise AssertionError(f"completing the chore did not use a pad: {left} {moved}")

            # Cron: steps, ranges and lists are read, and the next time is the
            # first one after now in local time; an expression naming no time is
            # refused, from the API too.
            import datetime
            assert post(base, "/api/scheduler/chores", {"title": "Every quarter hour", "kind": "cron", "value": "*/15 * * * *"})["ok"]
            assert post(base, "/api/scheduler/chores", {"title": "Weekday mornings", "kind": "cron", "value": "30 9 * * 1-5"})["ok"]
            assert post(base, "/api/scheduler/chores", {"title": "Sundays", "kind": "cron", "value": "0 8 * * 7"})["ok"]
            with sqlite3.connect(db) as conn:
                due = dict(conn.execute("SELECT title, next_due_epoch FROM chores WHERE schedule_kind='cron'").fetchall())
            now = time.time()
            quarter = datetime.datetime.fromtimestamp(due["Every quarter hour"])
            if not (0 < due["Every quarter hour"] - now <= 900 and quarter.minute % 15 == 0):
                raise AssertionError(f"*/15 is due at {quarter}")
            morning = datetime.datetime.fromtimestamp(due["Weekday mornings"])
            if morning.weekday() > 4 or (morning.hour, morning.minute) != (9, 30) or not 0 < due["Weekday mornings"] - now <= 4 * 86400:
                raise AssertionError(f"30 9 * * 1-5 is due at {morning}")
            sunday = datetime.datetime.fromtimestamp(due["Sundays"])
            if sunday.weekday() != 6 or sunday.hour != 8:
                raise AssertionError(f"0 8 * * 7 is due at {sunday}")
            # A chore is edited and deleted from its row: renaming it does not
            # move when it is due; deleting it takes its history with it.
            def form(path, fields):
                req = urllib.request.Request(base + path, method="POST",
                    data=urllib.parse.urlencode(dict(fields, csrf=CSRF)).encode())
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                with open_url(req, timeout=20) as response:
                    return response.read().decode("utf-8", "replace")
            with sqlite3.connect(db) as conn:
                sunday_id = conn.execute("SELECT id FROM chores WHERE title='Sundays'").fetchone()[0]
            assert_contains(get(base, f"/scheduler/chores/edit?id={sunday_id}"), ["Sundays", "0 8 * * 7"], "the chore's edit page")
            form(f"/scheduler/chores/edit?id={sunday_id}", {"title": "Sunday mornings", "kind": "cron", "value": "0 8 * * 7",
                                                             "interval_hours": "0", "priority": "low"})
            with sqlite3.connect(db) as conn:
                row = conn.execute("SELECT title, priority, next_due_epoch FROM chores WHERE id=?", (sunday_id,)).fetchone()
            if row != ("Sunday mornings", "low", due["Sundays"]):
                raise AssertionError(f"the edited chore: {row} (due was {due['Sundays']})")
            assert_contains(form("/scheduler/chores/delete", {"id": str(sunday_id)}), ["Chore deleted"], "a deleted chore")
            with sqlite3.connect(db) as conn:
                if conn.execute("SELECT COUNT(*) FROM chores WHERE id=?", (sunday_id,)).fetchone()[0] != 0:
                    raise AssertionError("the deleted chore is still there")
            request = urllib.request.Request(base + "/api/scheduler/chores", method="POST",
                data=urllib.parse.urlencode({"title": "Never", "kind": "cron", "value": "61 * * * *", "csrf": CSRF}).encode())
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
            try:
                with open_url(request, timeout=20) as response:
                    raise AssertionError(f"a cron naming no time was answered {response.status}")
            except urllib.error.HTTPError as error:
                if error.code != 400 or "names no time" not in error.read().decode():
                    raise AssertionError(f"a cron naming no time was answered {error.code}")

            # A preset chore the person deletes stays deleted: the next start
            # does not seed it again, and one they rename is not added back
            # under its old title.
            # @verifies SCHED-0006
            with sqlite3.connect(db) as conn:
                water = conn.execute("SELECT id FROM chores WHERE title='Water change'").fetchone()
                glass = conn.execute("SELECT id FROM chores WHERE title='Clean the glass'").fetchone()
            if not water or not glass:
                raise AssertionError("the aquarium's preset chores were not seeded")
            assert_contains(form("/scheduler/chores/delete", {"id": str(water[0])}), ["Chore deleted"], "a deleted preset chore")
            form(f"/scheduler/chores/edit?id={glass[0]}", {"title": "Clean the front glass", "kind": "interval",
                                                           "interval_hours": "336", "priority": "low"})
            stop(process)
            process = start()
            wait_for(base)
            with sqlite3.connect(db) as conn:
                titles = [r[0] for r in conn.execute("SELECT title FROM chores")]
            if "Water change" in titles:
                raise AssertionError("a preset chore the person deleted came back at the next start")
            if "Clean the glass" in titles or "Clean the front glass" not in titles:
                raise AssertionError(f"a renamed preset chore was added back under its old title: {titles}")
            if "Test the water" not in titles:
                raise AssertionError(f"a preset chore the person kept is gone: {titles}")
        finally:
            stop(process)
    if second_word.exists() or (tmp_first_word.exists() and not had_first_word):
        raise AssertionError(f"a directory was made from a word of the workspace's path: {second_word} or {tmp_first_word}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
