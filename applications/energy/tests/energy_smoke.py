#!/usr/bin/env python3
"""Smoke test for the RoboHub energy application.

Builds the service, starts it against a temporary workspace with no hardware,
walks every page, exercises the CSRF-protected forms, injects a scripted fault,
reads the SSE stream, clears the fault, switches to off-grid mode, and checks
the SQLite/WAL telemetry store.
"""

import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve()
APP = HERE.parents[1]
ROBOHUB = APP.parents[1]
PROJECTS = ROBOHUB.parent
RHO = PROJECTS / "rho" / "bin" / "rho"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(base: str) -> None:
    deadline = time.time() + 25
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise SystemExit(f"energy did not start at {base}")


def get(base: str, path: str) -> str:
    with urllib.request.urlopen(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def csrf(base: str, path: str = "/settings") -> str:
    html = get(base, path)
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    if not match:
        raise AssertionError(f"no CSRF token on {path}")
    return match.group(1)


def post(base: str, path: str, fields: dict, token: str = "") -> str:
    fields = dict(fields)
    if token:
        fields["csrf"] = token
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def post_hx(base: str, path: str, fields: dict) -> str:
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("HX-Request", "true")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode()


def post_json(base: str, path: str, fields: dict) -> dict:
    body = json.dumps(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read())


def state(base: str) -> dict:
    return json.loads(get(base, "/api/energy/state"))


def assert_contains(haystack: str, needles: list, label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} does not contain {needle!r}")


def build() -> Path:
    binary = APP / "build" / "energy"
    rho = str(RHO) if RHO.exists() else "rho"
    result = subprocess.run([rho, "build", str(APP)], cwd=ROBOHUB, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise SystemExit("energy build failed:\n" + result.stdout + result.stderr)
    if not binary.exists():
        raise SystemExit(f"energy build wrote no binary at {binary}")
    return binary


def main() -> int:
    binary = build()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="energy-") as workspace:
        telemetry = Path(workspace) / "data" / "telemetry.db"
        env = dict(os.environ)
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(APP / "module.yml")
        env["ROBOHUB_MESH_TELEMETRY_DB"] = str(telemetry)
        env["ROBOHUB_DRIVER_MODE"] = "mock"
        env["XDG_STATE_HOME"] = str(Path(workspace) / "state")
        env["RHO_HTTP_ADDR"] = f":{port}"
        process = subprocess.Popen([str(binary)], cwd=APP, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        try:
            wait_for(base)
            for page in ["/", "/sources", "/storage", "/grid", "/loads",
                         "/modes", "/safety", "/faults", "/events", "/settings",
                         "/docs", "/expenses", "/scheduler", "/widgets"]:
                if urllib.request.urlopen(base + page, timeout=10).status != 200:
                    raise AssertionError(f"{page} did not answer")

            home = get(base, "/")
            assert_contains(home, ["Dashboard", "Generation", "Battery SoC",
                                   "Power faults", "Simulation", "Inventory",
                                   "Scheduler", "Widgets"], "widget dashboard")
            module_page = get(base, "/expenses")
            assert_contains(module_page, ["Sources", "Storage", "Inventory"],
                            "module host shell")
            assert_contains(get(base, "/scheduler"), ["Sources", "Scheduler"],
                            "scheduler host shell")
            assert_contains(get(base, "/widgets"), ["Sources", "Widgets"],
                            "widgets host shell")

            first = state(base)
            if first["driver"] != "mock" or not first["simulation"]:
                raise AssertionError("the test expected the mock driver")
            if first["mode"] != "hybrid":
                raise AssertionError("a new site should start hybrid")
            if first["faults"] != 0:
                raise AssertionError("a seeded site should have no active faults")
            if float(first["soc_pct"]) < 40:
                raise AssertionError("the seeded bank should start above 40%")
            for key in ["battery_temp_limit_c", "solar_temp_limit_c",
                        "grid_min_voltage_v", "grid_max_voltage_v"]:
                if float(first[key]) <= 0:
                    raise AssertionError(f"{key} should be a real threshold")

            ingested = post_json(base, "/api/energy/ingest", {
                "type": "source", "name": "South roof — string A",
                "power_w": 1800, "voltage_v": 400, "temperature_c": 34,
            })
            if not ingested.get("ok") or ingested.get("id") != 1:
                raise AssertionError("JSON ingestion did not match the seeded source")

            token = csrf(base, "/sources")
            post(base, "/sources/add", {
                "name": "North array", "kind": "solar_pv", "bus": "dc-bus-3",
                "address": "192.168.10.44", "rated_kw": "3.2",
                "protocol": "Modbus/SunSpec",
            }, token)
            assert_contains(get(base, "/sources"), ["North array", "3.2 kW"],
                            "sources")

            token = csrf(base, "/settings")
            post(base, "/settings", {
                "driver_mode": "mock", "site_name": "Garden",
                "refresh_seconds": "2", "mesh_url": "",
                "mesh_project": "default", "mesh_token": "",
                "sim_fault": "none",
            }, token)
            saved = state(base)
            if saved["site"] != "Garden":
                raise AssertionError("settings were not saved")

            settings_html = get(base, "/settings")
            if 'name="level"' not in settings_html:
                raise AssertionError("the Logging form is missing")
            log_file = Path(workspace) / "logs" / "energy.log"
            token = csrf(base, "/settings")
            post(base, "/settings/log", {
                "level": "debug", "format": "json", "file": str(log_file),
                "max_bytes": "65536", "keep": "3", "stderr": "1",
            }, token)
            if not log_file.exists():
                raise AssertionError("the application log file was not created")
            if "logging settings updated" not in log_file.read_text():
                raise AssertionError("the log settings event was not written")
            if saved["project"] != "energy-sim":
                raise AssertionError("simulation telemetry project should be derived")

            token = csrf(base, "/settings")
            post(base, "/settings/sim-toggle", {"mode": "hardware"}, token)
            switched = state(base)
            if switched["driver"] != "hardware" or switched["simulation"]:
                raise AssertionError("the simulation toggle did not switch to real-time")
            con = sqlite3.connect(Path(workspace) / "data" / "app.db")
            try:
                source = con.execute(
                    "select source_kind, source from widgets where title = 'Generation'"
                ).fetchone()
            finally:
                con.close()
            if source != ("manual", ""):
                raise AssertionError("real-time mode did not reset the simulated source")
            token = csrf(base, "/settings")
            post(base, "/settings/sim-toggle", {"mode": "mock"}, token)
            if not state(base)["simulation"]:
                raise AssertionError("the simulation toggle did not switch back")
            con = sqlite3.connect(Path(workspace) / "data" / "app.db")
            try:
                source = con.execute(
                    "select source_kind, source from widgets where title = 'Generation'"
                ).fetchone()
            finally:
                con.close()
            if source != ("mesh", "energy.generation"):
                raise AssertionError("simulation mode did not preselect the simulated source")

            refreshed = post_json(base, "/api/energy/widgets/refresh", {})
            if not refreshed.get("ok"):
                raise AssertionError("the widget refresh endpoint failed")

            heartbeat = get(base, "/api/energy/heartbeat")
            if "Simulation" not in heartbeat:
                raise AssertionError("the simulation heartbeat is missing")
            settings_html = get(base, "/settings")
            if 'name="project"' in settings_html:
                raise AssertionError("telemetry project must not be an input")
            if 'name="mesh_project"' not in settings_html:
                raise AssertionError("the Mesh project select is missing")
            moved = post_hx(base, "/widgets/move", {"id": "1", "delta": "1"})
            if 'id="widget-cards"' not in moved or "<html" in moved:
                raise AssertionError("widget movement did not return an in-place grid")

            sim_sources = get(base, "/api/energy/sim/gateway/sources")
            assert_contains(sim_sources, ["energy.generation", "energy.faults"],
                            "simulated Mesh sources")
            if not get(base, "/api/energy/sim/gateway/latest?source=energy.soc"):
                raise AssertionError("the simulated SoC source has no value")
            edit = get(base, "/widgets/edit?id=1")
            if 'value="energy.generation"' not in edit or "selected" not in edit:
                raise AssertionError("the simulated source is not preselected")

            token = csrf(base, "/safety")
            post(base, "/safety", {
                "mode": "hybrid", "grid_forming": "1", "zero_export": "1",
                "peak_shaving": "1", "tariff_optimization": "1",
                "reserve_soc_pct": "30.0", "load_shed_soc_pct": "20.0",
                "generator_start_soc_pct": "12.0",
                "generator_stop_soc_pct": "45.0",
                "charge_limit_a": "40.0", "discharge_limit_a": "100.0",
                "charge_voltage_v": "57.0", "discharge_cutoff_v": "44.5",
                "export_limit_w": "0", "solar_temp_limit_c": "70.0",
                "battery_temp_limit_c": "42.0",
                "source_over_voltage_v": "580.0",
                "source_over_current_a": "18.0",
                "battery_cell_delta_mv": "150",
                "grid_min_voltage_v": "210.0", "grid_max_voltage_v": "250.0",
                "grid_min_frequency_hz": "49.60",
                "grid_max_frequency_hz": "50.40",
            }, token)
            policy = state(base)
            if float(policy["reserve_soc_pct"]) != 30.0:
                raise AssertionError("the safety reserve was not saved")
            if float(policy["battery_temp_limit_c"]) != 42.0:
                raise AssertionError("the battery temperature limit was not saved")

            rejected = post(base, "/modes/set", {"mode": "on_grid"})
            if "Refused" not in rejected:
                raise AssertionError("a POST without a CSRF token should be refused")

            token = csrf(base, "/modes")
            post(base, "/modes/set", {"mode": "off_grid"}, token)
            if state(base)["mode"] != "off_grid":
                raise AssertionError("the mode did not switch to off-grid")

            post(base, "/api/energy/sim/fault", {"fault": "battery_low"})
            deadline = time.time() + 12
            low = state(base)
            while time.time() < deadline and not (low["generator"] and low["load_shed"]):
                time.sleep(0.5)
                low = state(base)
            if not low["generator"]:
                raise AssertionError("the generator should start on a low battery")
            if not low["load_shed"]:
                raise AssertionError("the discretionary loads should be shed")
            assert_contains(get(base, "/faults"), ["state of charge"], "faults")
            assert_contains(get(base, "/modes"), ["running", "active"], "off-grid modes")

            post(base, "/api/energy/sim/fault", {"fault": "none"})
            token = csrf(base, "/modes")
            post(base, "/modes/set", {"mode": "hybrid"}, token)
            post(base, "/api/energy/ingest", {
                "type": "battery", "name": "Main LiFePO4 bank",
                "soc_pct": "60", "voltage_v": "52.0",
                "temperature_c": "25", "cell_min_v": "3.30",
                "cell_max_v": "3.32",
            })
            time.sleep(3)

            post(base, "/api/energy/sim/fault", {"fault": "pv_overtemp"})
            time.sleep(4)
            badge = get(base, "/")
            assert_contains(badge, ["Power faults", "fault"], "fault widget")
            assert_contains(get(base, "/faults"), ["back-sheet temperature"],
                            "fault badge detail")
            if not telemetry.exists():
                raise AssertionError("the telemetry store was not written")
            con = sqlite3.connect(telemetry)
            try:
                journal = con.execute("pragma journal_mode").fetchone()[0]
                if journal.lower() != "wal":
                    raise AssertionError(f"telemetry is not in WAL mode: {journal}")
                rows = con.execute(
                    "select severity, message from telemetry_fault "
                    "where project = 'energy-sim'").fetchall()
                if not rows:
                    raise AssertionError("no power fault reached the telemetry store")
                if not any("back-sheet" in message for _, message in rows):
                    raise AssertionError("the over-temperature fault was not recorded")
            finally:
                con.close()

            request = urllib.request.Request(base + "/energy/stream")
            with urllib.request.urlopen(request, timeout=5) as response:
                chunk = response.read(6000).decode("utf-8", "replace")
            assert_contains(chunk, ["event: faults", "event: faults-rows"],
                            "fault SSE stream")

            post(base, "/api/energy/sim/fault", {"fault": "none"})
            time.sleep(4)
            if "No power faults" not in get(base, "/"):
                raise AssertionError("clearing the scripted fault did not clear the badge")

            events = get(base, "/events")
            assert_contains(events, ["Safety policy updated",
                                     "Operating mode set to Off-grid (island)",
                                     "Scripted fault presented"], "events")

            db = Path(workspace) / "data" / "app.db"
            if not db.exists():
                raise AssertionError("the application database is not in its workspace")
            energy_live = Path(workspace) / "data" / "energy-live.events"
            if not energy_live.exists():
                raise AssertionError("the energy SSE feed was not written")
            notification_live = Path(workspace) / "data" / "live.events"
            if notification_live.exists() and "dashboard" in notification_live.read_text():
                raise AssertionError("the energy dashboard is writing to the notifications feed")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
