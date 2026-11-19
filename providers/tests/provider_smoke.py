#!/usr/bin/env python3
"""The alert providers' tests: what they run curl with, and what they refuse.

The harness (`harness/`) is a program that binds every alert channel and raises
one alert when it is asked to. Each case writes the channel's settings into the
workspace's bind.conf, raises an alert, and reads what a curl of the test's own,
first on PATH, was run with: its arguments, and the files they name, as they were
while curl ran.

What is checked, for each channel:

- a secret setting (an address, a token, a chat id, a password) is never one of
  curl's arguments, which any user of the machine can list with `ps`; it is in
  a configuration file only the owner can read, and that file is gone after the
  delivery;
- a malformed setting is refused, with no curl run, rather than guessed at;
- an alert whose text tries to change where or how it is delivered (a line that
  looks like another option, header or alert) is delivered as text.

Usage: provider_smoke.py webhook|telegram|email|log
"""

import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness"
ROBOHUB = HERE.parents[1]
PROJECTS = ROBOHUB.parent
RHO = str(PROJECTS / "rho" / "bin" / "rho") if (PROJECTS / "rho" / "bin" / "rho").exists() else "rho"

PROVIDERS = ["webhook", "telegram", "email", "log"]

FAKE_CURL = r'''#!/usr/bin/env python3
import json, os, stat, sys
args = sys.argv[1:]
record = {"argv": args, "files": {}}
for index, arg in enumerate(args):
    candidates = []
    if arg in ("-K", "--config", "-T", "--upload-file") and index + 1 < len(args):
        candidates.append(args[index + 1])
    at = arg.find("@")
    while at >= 0:
        candidates.append(arg[at + 1:])
        at = arg.find("@", at + 1)
    for path in candidates:
        if os.path.isfile(path):
            mode = stat.S_IMODE(os.stat(path).st_mode)
            with open(path, encoding="utf-8", errors="replace") as handle:
                record["files"][path] = {"mode": mode, "text": handle.read()}
with open(os.environ["CURL_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\n")
sys.exit(int(os.environ.get("CURL_EXIT", "0")))
'''


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def build() -> Path:
    result = subprocess.run([RHO, "build", str(HARNESS)], cwd=ROBOHUB, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise SystemExit("the harness did not build:\n" + result.stdout + result.stderr)
    return HARNESS / "build" / "robohub-provider-harness"


def config_value(text: str, option: str) -> list:
    """Every value an option has in a curl configuration file, unquoted."""
    values = []
    for line in text.splitlines():
        name, _, rest = line.partition("=")
        if name.strip() != option:
            continue
        rest = rest.strip()
        if not (rest.startswith('"') and rest.endswith('"')):
            raise AssertionError(f"{option} is not quoted: {line!r}")
        out, i, body = [], 0, rest[1:-1]
        while i < len(body):
            if body[i] == "\\":
                i += 1
                out.append(body[i])
            elif body[i] == '"':
                raise AssertionError(f"an unescaped quote ends {option} early: {line!r}")
            else:
                out.append(body[i])
            i += 1
        values.append("".join(out))
    return values


class Harness:
    def __init__(self, binary: Path, root: str):
        self.workspace = os.path.join(root, "workspace")
        self.bin = os.path.join(root, "bin")
        self.curl_log = os.path.join(root, "curl.log")
        os.makedirs(self.workspace)
        os.makedirs(self.bin)
        curl = os.path.join(self.bin, "curl")
        with open(curl, "w", encoding="utf-8") as handle:
            handle.write(FAKE_CURL)
        os.chmod(curl, 0o755)
        self.port = free_port()
        env = dict(os.environ)
        env.update({
            "HOME": root,
            "RHO_APP_WORKSPACE": self.workspace,
            "ROBOHUB_APP_WORKSPACE": self.workspace,
            "RHO_HTTP_ADDR": f"127.0.0.1:{self.port}",
            "PATH": self.bin + os.pathsep + env.get("PATH", ""),
            "CURL_LOG": self.curl_log,
        })
        self.process = subprocess.Popen([str(binary)], env=env, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=1).close()
                return
            except OSError:
                time.sleep(0.1)
        raise SystemExit("the harness did not start")

    def close(self) -> None:
        self.process.terminate()
        self.process.wait(timeout=10)

    def raise_alert(self, provider: str, settings: dict, level: str = "WARNING",
                    message: str = "Water at 29.1", metadata: str = '{"rule":"too-warm"}'):
        """Raise one alert with only `provider` on; (channels accepted, curl runs)."""
        lines = []
        for other in PROVIDERS:
            if other != provider:
                lines.append(f"robohub-provider-{other}.enabled=false")
        for key, value in settings.items():
            lines.append(f"robohub-provider-{provider}.{key}={value}")
        with open(os.path.join(self.workspace, "bind.conf"), "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        if os.path.exists(self.curl_log):
            os.remove(self.curl_log)
        query = urllib.parse.urlencode({"level": level, "message": message, "metadata": metadata})
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/raise?{query}", timeout=30) as response:
            sent = int(response.read().decode().strip() or "0")
        runs = []
        if os.path.exists(self.curl_log):
            with open(self.curl_log, encoding="utf-8") as handle:
                runs = [json.loads(line) for line in handle if line.strip()]
        return sent, runs

    def leftovers(self, secrets: list) -> list:
        """Files under the workspace's alerts folder that still hold a secret."""
        found = []
        folder = os.path.join(self.workspace, "alerts")
        for root, _, files in os.walk(folder):
            for name in files:
                path = os.path.join(root, name)
                with open(path, encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                if any(secret in text for secret in secrets):
                    found.append(os.path.relpath(path, self.workspace))
        return found


def one_run(runs: list, label: str) -> dict:
    if len(runs) != 1:
        raise AssertionError(f"{label}: curl ran {len(runs)} times")
    return runs[0]


def no_secret_on_argv(run: dict, secrets: list, label: str) -> None:
    argv = "\n".join(run["argv"])
    for secret in secrets:
        if secret in argv:
            raise AssertionError(f"{label}: {secret!r} is on curl's command line: {run['argv']}")


def config_of(run: dict, label: str) -> str:
    """The -K file curl was given: owner-only, and its text."""
    argv = run["argv"]
    if "-K" not in argv:
        raise AssertionError(f"{label}: curl was given no configuration file: {argv}")
    path = argv[argv.index("-K") + 1]
    held = run["files"].get(path)
    if not held:
        raise AssertionError(f"{label}: the configuration file was not there while curl ran")
    if held["mode"] & 0o077:
        raise AssertionError(f"{label}: the configuration file is mode {oct(held['mode'])}")
    return held["text"]


def refused(h: Harness, provider: str, settings: dict, label: str, **alert) -> None:
    sent, runs = h.raise_alert(provider, settings, **alert)
    if sent != 0 or runs:
        raise AssertionError(f"{label}: accepted ({sent}) with curl run {len(runs)} times")


def webhook(h: Harness) -> None:
    url = 'https://hooks.example/T0K3N-in-the-path?key=s3cret&x="q"\\b'
    secrets = ["T0K3N-in-the-path", "s3cret", "hooks.example", "Bearer abc-auth-secret"]
    sent, runs = h.raise_alert("webhook", {"url": url, "authorization": "Bearer abc-auth-secret"})
    run = one_run(runs, "webhook")
    if sent != 1:
        raise AssertionError("webhook: a delivery curl accepted was not counted")
    no_secret_on_argv(run, secrets, "webhook")
    config = config_of(run, "webhook")
    if config_value(config, "url") != [url]:
        raise AssertionError(f"webhook: the configuration names {config_value(config, 'url')}")
    if "Authorization: Bearer abc-auth-secret" not in config_value(config, "header"):
        raise AssertionError("webhook: the Authorization header is not in the configuration")
    if h.leftovers(secrets):
        raise AssertionError(f"webhook: a secret is left behind in {h.leftovers(secrets)}")

    # An alert that tries to be options of curl, or another address, is text in
    # the body and nowhere else.
    evil = 'x\n-o\n/tmp/pwned\nurl = "https://evil.example"'
    sent, runs = h.raise_alert("webhook", {"url": url, "content_type": "application/json"},
                               message=evil, metadata=evil)
    run = one_run(runs, "webhook evil")
    if any("evil.example" in a or "/tmp/pwned" in a for a in run["argv"]):
        raise AssertionError(f"webhook: the alert reached curl's arguments: {run['argv']}")
    if config_value(config_of(run, "webhook evil"), "url") != [url]:
        raise AssertionError("webhook: the alert changed where it is delivered")
    bodies = [f["text"] for p, f in run["files"].items() if p.endswith(".body")]
    if not bodies or json.loads(bodies[0])["message"] != evil:
        raise AssertionError(f"webhook: the body is not the alert as JSON: {bodies}")

    # Malformed settings are refused rather than guessed at.
    for bad in ("", "ftp://hooks.example/x", "file:///etc/passwd", "-K/etc/passwd", "hooks.example/x"):
        refused(h, "webhook", {"url": bad}, f"webhook url {bad!r}")


def telegram(h: Harness) -> None:
    token, chat = "123456:AAH-secret_TOKEN", "-1009876543"
    sent, runs = h.raise_alert("telegram", {"bot_token": token, "chat_id": chat})
    run = one_run(runs, "telegram")
    if sent != 1:
        raise AssertionError("telegram: a delivery curl accepted was not counted")
    no_secret_on_argv(run, [token, chat, "9876543"], "telegram")
    config = config_of(run, "telegram")
    if config_value(config, "url") != [f"https://api.telegram.org/bot{token}/sendMessage"]:
        raise AssertionError(f"telegram: the configuration names {config_value(config, 'url')}")
    if config_value(config, "data-urlencode") != [f"chat_id={chat}"]:
        raise AssertionError(f"telegram: the chat is {config_value(config, 'data-urlencode')}")
    if h.leftovers([token, chat]):
        raise AssertionError(f"telegram: a secret is left behind in {h.leftovers([token, chat])}")

    # Text that looks like another chat or option is text.
    evil = "hello\nchat_id=666\n-K\n/etc/passwd"
    sent, runs = h.raise_alert("telegram", {"bot_token": token, "chat_id": chat}, message=evil)
    run = one_run(runs, "telegram evil")
    if any("666" in a or "/etc/passwd" in a for a in run["argv"]):
        raise AssertionError(f"telegram: the alert reached curl's arguments: {run['argv']}")
    if config_value(config_of(run, "telegram evil"), "data-urlencode") != [f"chat_id={chat}"]:
        raise AssertionError("telegram: the alert changed the chat")
    texts = [f["text"] for p, f in run["files"].items() if p.endswith(".txt")]
    if not texts or evil not in texts[0]:
        raise AssertionError(f"telegram: the text is not the alert: {texts}")

    for key, bad in (("bot_token", ""), ("bot_token", "123/../evil"), ("bot_token", 'a"b'),
                     ("bot_token", "a b"), ("chat_id", ""), ("chat_id", "1&text=x"),
                     ("chat_id", "@channel")):
        settings = {"bot_token": token, "chat_id": chat}
        settings[key] = bad
        refused(h, "telegram", settings, f"telegram {key} {bad!r}")


def email(h: Harness) -> None:
    password = 'pa"ss\\word secret'
    settings = {"mode": "smtp", "smtp_host": "mail.example.org", "smtp_port": "587",
                "smtp_security": "starttls", "smtp_user": "alerts@example.org",
                "smtp_pass": password, "to_address": "ops-person@example.org",
                "from_address": "aquarium@example.org"}
    sent, runs = h.raise_alert("email", settings)
    run = one_run(runs, "email")
    if sent != 1:
        raise AssertionError("email: a delivery curl accepted was not counted")
    secrets = ["ops-person@example.org", "alerts@example.org", "pa\"ss", "mail.example.org"]
    no_secret_on_argv(run, secrets, "email")
    config = config_of(run, "email")
    expected = {"url": ["smtp://mail.example.org:587"], "mail-rcpt": ["ops-person@example.org"],
                "mail-from": ["aquarium@example.org"], "user": [f"alerts@example.org:{password}"]}
    for option, values in expected.items():
        if config_value(config, option) != values:
            raise AssertionError(f"email: {option} is {config_value(config, option)}")
    if "--ssl-reqd" not in run["argv"]:
        raise AssertionError("email: starttls no longer requires TLS")
    if h.leftovers(["pa\"ss", "ops-person@example.org"]):
        raise AssertionError("email: the message or the login is left behind")

    # An alert whose text tries to add a recipient is text: the headers stay three.
    evil = "warm\nBcc: thief@evil.example\n"
    sent, runs = h.raise_alert("email", dict(settings, subject_template="{message}"),
                               message=evil, metadata='{"rule":"x\\nBcc: thief@evil.example"}')
    run = one_run(runs, "email evil")
    config = config_of(run, "email evil")
    if config_value(config, "mail-rcpt") != ["ops-person@example.org"]:
        raise AssertionError("email: the alert added a recipient")
    mails = [f["text"] for p, f in run["files"].items() if p.endswith(".eml")]
    headers = mails[0].split("\n\n", 1)[0] if mails else ""
    if not mails or "\nBcc:" in "\n" + headers:
        raise AssertionError(f"email: the alert wrote a header: {headers!r}")

    for key, bad in (("smtp_host", ""), ("smtp_host", "evil.example/path"),
                     ("smtp_host", "user@evil.example"), ("smtp_host", "a b"),
                     ("smtp_port", "25/x"), ("smtp_port", "587 -v")):
        refused(h, "email", dict(settings, **{key: bad}), f"email {key} {bad!r}")
    refused(h, "email", dict(settings, mode="sendmail"), "email mode 'sendmail'")
    refused(h, "email", dict(settings, to_address=""), "email with no recipient")


def log(h: Harness) -> None:
    path = os.path.join(h.workspace, "alerts-test.log")
    evil = "Water at 29.1\n[CRITICAL] forged alert"
    sent, runs = h.raise_alert("log", {"path": path}, message=evil, metadata="a\r\nb")
    if sent != 1 or runs:
        raise AssertionError(f"log: accepted {sent}, curl ran {len(runs)} times")
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    if len(lines) != 1 or not lines[0].startswith("[WARNING] Water at 29.1"):
        raise AssertionError(f"log: one alert wrote {lines}")


def main() -> int:
    wanted = sys.argv[1:] or PROVIDERS
    binary = build()
    for provider in wanted:
        with tempfile.TemporaryDirectory(prefix=f"provider-{provider}-") as root:
            harness = Harness(binary, root)
            try:
                globals()[provider](harness)
            finally:
                harness.close()
        print(f"{provider}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
