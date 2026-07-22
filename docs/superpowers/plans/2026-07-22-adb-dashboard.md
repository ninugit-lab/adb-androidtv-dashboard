# ADB AndroidTV Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Django app (no venv, vendored packages) with a
dashboard for sending arbitrary ADB shell commands to multiple configurable
AndroidTV devices, plus a `/config` page to manage devices, commands, and
their assignment.

**Architecture:** Django project (`adbdash`) with a single app (`dashboard`).
Persistence is a hand-rolled JSON store (`config_store.py` + `config.json`),
not Django models. ADB communication goes through `pure-python-adb`
(`ppadb`), wrapped in `adb_client.py`. Dashboard buttons call a JSON endpoint
via `fetch()`; the config page uses plain HTML forms (POST + redirect).

**Tech Stack:** Django (vendored into `./vendor`, no venv), `pure-python-adb`
(`ppadb`), vanilla JS, no database usage beyond Django's required
`DATABASES` setting.

**Spec:** `docs/superpowers/specs/2026-07-22-adb-dashboard-design.md`

---

## File Structure

```
adbapp/
├── requirements.txt          # Django, pure-python-adb
├── setup.sh                  # pip install --target=./vendor -r requirements.txt
├── .gitignore                # vendor/, config.json, db.sqlite3, __pycache__
├── manage.py                 # inserts ./vendor onto sys.path before Django import
├── adbdash/                  # Django project package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── dashboard/                 # Django app
    ├── __init__.py
    ├── apps.py
    ├── admin.py               # untouched default
    ├── models.py               # untouched default (unused, no models)
    ├── config_store.py         # JSON persistence for devices/commands
    ├── adb_client.py           # ppadb wrapper: connect/run/status
    ├── views.py                # dashboard, run_command, config_view
    ├── urls.py
    ├── templates/dashboard/
    │   ├── index.html
    │   └── config.html
    ├── static/dashboard/
    │   └── style.css
    └── tests/
        ├── __init__.py
        ├── test_config_store.py
        ├── test_adb_client.py
        └── test_views.py
```

---

### Task 1: Standalone package vendoring

**Files:**
- Create: `requirements.txt`
- Create: `setup.sh`
- Create: `.gitignore`

- [ ] **Step 1: Create `requirements.txt`**

```
Django>=5.0,<6.0
pure-python-adb>=0.3.0,<1.0
```

- [ ] **Step 2: Create `setup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
pip install --target=./vendor -r requirements.txt
echo "Setup complete. Run: python manage.py runserver"
```

- [ ] **Step 3: Make it executable and run it**

Run: `chmod +x setup.sh && ./setup.sh`
Expected: pip installs Django and pure-python-adb (and their dependencies)
into `./vendor`, ending with "Setup complete. Run: python manage.py
runserver".

- [ ] **Step 4: Verify vendoring worked**

Run: `ls vendor | grep -i django`
Expected: a `django` directory is listed.

- [ ] **Step 5: Create `.gitignore`**

```
vendor/
config.json
db.sqlite3
__pycache__/
*.pyc
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt setup.sh .gitignore
git commit -m "Add standalone vendor/ package setup"
```

---

### Task 2: Bootstrap Django project skeleton

**Files:**
- Create: `manage.py`
- Create: `adbdash/__init__.py`, `adbdash/settings.py`, `adbdash/urls.py`, `adbdash/wsgi.py`, `adbdash/asgi.py`

- [ ] **Step 1: Generate the project using the vendored Django**

Run: `PYTHONPATH=./vendor python3 -m django startproject adbdash .`
Expected: creates `adbdash/` (with `settings.py`, `urls.py`, `wsgi.py`,
`asgi.py`, `__init__.py`) and a default `manage.py` in the project root.

- [ ] **Step 2: Replace `manage.py` with a vendor-aware version**

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    vendor_path = str(Path(__file__).resolve().parent / "vendor")
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adbdash.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed in ./vendor? "
            "Run ./setup.sh first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Replace `adbdash/settings.py` content**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-secret-key-change-me"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "adbdash.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "adbdash.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "de-de"

TIME_ZONE = "Europe/Berlin"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

- [ ] **Step 4: Replace `adbdash/urls.py` with an empty placeholder**

```python
from django.urls import path

urlpatterns = []
```

- [ ] **Step 5: Verify the project boots**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
git add manage.py adbdash
git commit -m "Bootstrap Django project skeleton"
```

---

### Task 3: Create the dashboard app skeleton and wire it up

**Files:**
- Create: `dashboard/` (via `startapp`)
- Modify: `adbdash/settings.py` (`INSTALLED_APPS`)
- Modify: `adbdash/urls.py`
- Create: `dashboard/urls.py`
- Delete: `dashboard/tests.py` (default file, replaced by `dashboard/tests/` package)
- Create: `dashboard/tests/__init__.py`

- [ ] **Step 1: Generate the app**

Run: `python manage.py startapp dashboard`
Expected: creates `dashboard/` with `models.py`, `views.py`, `admin.py`,
`apps.py`, `tests.py`, `migrations/`.

- [ ] **Step 2: Add `dashboard` to `INSTALLED_APPS`**

In `adbdash/settings.py`, change:

```python
INSTALLED_APPS = [
    "django.contrib.staticfiles",
]
```

to:

```python
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "dashboard",
]
```

- [ ] **Step 3: Wire the app's URLs into the project**

Replace `adbdash/urls.py` with:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("dashboard.urls")),
]
```

- [ ] **Step 4: Create `dashboard/urls.py`**

```python
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("device/<str:device_id>/run/<str:command_id>/", views.run_command, name="run_command"),
    path("config/", views.config_view, name="config"),
]
```

- [ ] **Step 5: Replace the default `tests.py` with a `tests/` package**

Run: `rm dashboard/tests.py && mkdir -p dashboard/tests && touch dashboard/tests/__init__.py`

- [ ] **Step 6: Verify the project still boots**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Commit**

```bash
git add dashboard adbdash/settings.py adbdash/urls.py
git commit -m "Add dashboard app skeleton"
```

---

### Task 4: `config_store.py` — JSON persistence (TDD)

**Files:**
- Create: `dashboard/config_store.py`
- Test: `dashboard/tests/test_config_store.py`

- [ ] **Step 1: Write the failing tests**

Create `dashboard/tests/test_config_store.py`:

```python
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dashboard import config_store


class ConfigStoreTests(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.config_path = Path(self.tmp_dir.name) / "config.json"
        patcher = patch.object(config_store, "CONFIG_PATH", self.config_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_load_missing_file_returns_empty_structure(self):
        result = config_store.load()
        self.assertEqual(result, {"devices": [], "commands": []})

    def test_add_device_persists_to_file(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        self.assertEqual(device["name"], "Wohnzimmer")
        self.assertEqual(device["ip"], "192.168.1.50")
        self.assertEqual(device["port"], 5555)
        self.assertEqual(device["command_ids"], [])
        data = config_store.load()
        self.assertEqual(len(data["devices"]), 1)
        self.assertEqual(data["devices"][0]["id"], device["id"])

    def test_update_device_changes_fields(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        updated = config_store.update_device(
            device["id"], "Schlafzimmer", "192.168.1.51", 5556
        )
        self.assertEqual(updated["name"], "Schlafzimmer")
        self.assertEqual(updated["ip"], "192.168.1.51")
        self.assertEqual(updated["port"], 5556)

    def test_update_device_missing_raises_keyerror(self):
        with self.assertRaises(KeyError):
            config_store.update_device("nope", "X", "0.0.0.0", 1)

    def test_delete_device_removes_it(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        config_store.delete_device(device["id"])
        data = config_store.load()
        self.assertEqual(data["devices"], [])

    def test_add_command_persists_to_file(self):
        command = config_store.add_command("Netflix öffnen", "echo netflix")
        data = config_store.load()
        self.assertEqual(len(data["commands"]), 1)
        self.assertEqual(data["commands"][0]["id"], command["id"])

    def test_update_command_changes_fields(self):
        command = config_store.add_command("Netflix öffnen", "echo netflix")
        updated = config_store.update_command(command["id"], "YouTube öffnen", "echo yt")
        self.assertEqual(updated["name"], "YouTube öffnen")
        self.assertEqual(updated["cmd"], "echo yt")

    def test_delete_command_removes_it_and_unassigns(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        command = config_store.add_command("Netflix öffnen", "echo netflix")
        config_store.assign_command(device["id"], command["id"])
        config_store.delete_command(command["id"])
        data = config_store.load()
        self.assertEqual(data["commands"], [])
        self.assertEqual(data["devices"][0]["command_ids"], [])

    def test_assign_and_unassign_command(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        command = config_store.add_command("Netflix öffnen", "echo netflix")
        config_store.assign_command(device["id"], command["id"])
        data = config_store.load()
        self.assertEqual(data["devices"][0]["command_ids"], [command["id"]])
        config_store.unassign_command(device["id"], command["id"])
        data = config_store.load()
        self.assertEqual(data["devices"][0]["command_ids"], [])

    def test_get_device_commands_returns_assigned_commands(self):
        device = config_store.add_device("Wohnzimmer", "192.168.1.50", 5555)
        command = config_store.add_command("Netflix öffnen", "echo netflix")
        config_store.assign_command(device["id"], command["id"])
        commands = config_store.get_device_commands(device["id"])
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["id"], command["id"])

    def test_get_device_and_get_command_return_none_when_missing(self):
        self.assertIsNone(config_store.get_device("nope"))
        self.assertIsNone(config_store.get_command("nope"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test dashboard.tests.test_config_store -v 2`
Expected: FAIL / ERROR — `config_store.py` does not exist yet
(`ModuleNotFoundError`).

- [ ] **Step 3: Implement `dashboard/config_store.py`**

```python
import json
import uuid
from pathlib import Path
from threading import Lock

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

_lock = Lock()


def load():
    if not CONFIG_PATH.exists():
        return {"devices": [], "commands": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with _lock:
        tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(CONFIG_PATH)


def get_device(device_id):
    data = load()
    return next((d for d in data["devices"] if d["id"] == device_id), None)


def get_command(command_id):
    data = load()
    return next((c for c in data["commands"] if c["id"] == command_id), None)


def get_device_commands(device_id):
    data = load()
    device = next((d for d in data["devices"] if d["id"] == device_id), None)
    if device is None:
        return []
    command_map = {c["id"]: c for c in data["commands"]}
    return [command_map[cid] for cid in device["command_ids"] if cid in command_map]


def add_device(name, ip, port):
    data = load()
    device = {
        "id": str(uuid.uuid4()),
        "name": name,
        "ip": ip,
        "port": port,
        "command_ids": [],
    }
    data["devices"].append(device)
    save(data)
    return device


def update_device(device_id, name, ip, port):
    data = load()
    for device in data["devices"]:
        if device["id"] == device_id:
            device["name"] = name
            device["ip"] = ip
            device["port"] = port
            save(data)
            return device
    raise KeyError(f"Device {device_id} not found")


def delete_device(device_id):
    data = load()
    data["devices"] = [d for d in data["devices"] if d["id"] != device_id]
    save(data)


def add_command(name, cmd):
    data = load()
    command = {"id": str(uuid.uuid4()), "name": name, "cmd": cmd}
    data["commands"].append(command)
    save(data)
    return command


def update_command(command_id, name, cmd):
    data = load()
    for command in data["commands"]:
        if command["id"] == command_id:
            command["name"] = name
            command["cmd"] = cmd
            save(data)
            return command
    raise KeyError(f"Command {command_id} not found")


def delete_command(command_id):
    data = load()
    data["commands"] = [c for c in data["commands"] if c["id"] != command_id]
    for device in data["devices"]:
        device["command_ids"] = [cid for cid in device["command_ids"] if cid != command_id]
    save(data)


def assign_command(device_id, command_id):
    data = load()
    for device in data["devices"]:
        if device["id"] == device_id:
            if command_id not in device["command_ids"]:
                device["command_ids"].append(command_id)
            save(data)
            return device
    raise KeyError(f"Device {device_id} not found")


def unassign_command(device_id, command_id):
    data = load()
    for device in data["devices"]:
        if device["id"] == device_id:
            device["command_ids"] = [cid for cid in device["command_ids"] if cid != command_id]
            save(data)
            return device
    raise KeyError(f"Device {device_id} not found")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test dashboard.tests.test_config_store -v 2`
Expected: all tests PASS (12 tests, OK).

- [ ] **Step 5: Commit**

```bash
git add dashboard/config_store.py dashboard/tests/test_config_store.py dashboard/tests/__init__.py
git commit -m "Add JSON-backed config_store for devices and commands"
```

---

### Task 5: `adb_client.py` — ppadb wrapper (TDD)

**Files:**
- Create: `dashboard/adb_client.py`
- Test: `dashboard/tests/test_adb_client.py`

- [ ] **Step 1: Write the failing tests**

Create `dashboard/tests/test_adb_client.py`:

```python
from unittest import TestCase
from unittest.mock import MagicMock, patch

from dashboard import adb_client


class AdbClientTests(TestCase):
    def setUp(self):
        adb_client._client = None
        self.addCleanup(setattr, adb_client, "_client", None)

    @patch("dashboard.adb_client.AdbClient")
    def test_connect_device_returns_device_on_success(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = True
        mock_device = MagicMock()
        mock_client.device.return_value = mock_device

        device = adb_client.connect_device("192.168.1.50", 5555)

        self.assertIs(device, mock_device)
        mock_client.remote_connect.assert_called_once_with("192.168.1.50", 5555)
        mock_client.device.assert_called_once_with("192.168.1.50:5555")

    @patch("dashboard.adb_client.AdbClient")
    def test_connect_device_returns_none_when_connect_fails(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = False

        device = adb_client.connect_device("192.168.1.50", 5555)

        self.assertIsNone(device)
        mock_client.device.assert_not_called()

    @patch("dashboard.adb_client.AdbClient")
    def test_connect_device_returns_none_on_exception(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.side_effect = ConnectionRefusedError("nope")

        device = adb_client.connect_device("192.168.1.50", 5555)

        self.assertIsNone(device)

    @patch("dashboard.adb_client.AdbClient")
    def test_check_status_true_when_connected(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = True
        mock_client.device.return_value = MagicMock()

        self.assertTrue(adb_client.check_status("192.168.1.50", 5555))

    @patch("dashboard.adb_client.AdbClient")
    def test_check_status_false_when_not_connected(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = False

        self.assertFalse(adb_client.check_status("192.168.1.50", 5555))

    @patch("dashboard.adb_client.AdbClient")
    def test_run_command_returns_output_on_success(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = True
        mock_device = MagicMock()
        mock_device.shell.return_value = "OK\n"
        mock_client.device.return_value = mock_device

        result = adb_client.run_command("192.168.1.50", 5555, "echo OK")

        self.assertEqual(result, {"ok": True, "output": "OK\n", "error": None})
        mock_device.shell.assert_called_once_with("echo OK")

    @patch("dashboard.adb_client.AdbClient")
    def test_run_command_returns_error_when_device_unreachable(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = False

        result = adb_client.run_command("192.168.1.50", 5555, "echo OK")

        self.assertEqual(
            result, {"ok": False, "output": None, "error": "Gerät nicht erreichbar"}
        )

    @patch("dashboard.adb_client.AdbClient")
    def test_run_command_returns_error_on_shell_exception(self, mock_adb_client_cls):
        mock_client = MagicMock()
        mock_adb_client_cls.return_value = mock_client
        mock_client.remote_connect.return_value = True
        mock_device = MagicMock()
        mock_device.shell.side_effect = RuntimeError("boom")
        mock_client.device.return_value = mock_device

        result = adb_client.run_command("192.168.1.50", 5555, "echo OK")

        self.assertEqual(result, {"ok": False, "output": None, "error": "boom"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test dashboard.tests.test_adb_client -v 2`
Expected: FAIL / ERROR — `adb_client.py` does not exist yet.

- [ ] **Step 3: Implement `dashboard/adb_client.py`**

```python
from ppadb.client import Client as AdbClient

_client = None


def get_client():
    global _client
    if _client is None:
        _client = AdbClient(host="127.0.0.1", port=5037)
    return _client


def connect_device(ip, port):
    client = get_client()
    try:
        connected = client.remote_connect(ip, port)
        if not connected:
            return None
        return client.device(f"{ip}:{port}")
    except Exception:
        return None


def check_status(ip, port):
    return connect_device(ip, port) is not None


def run_command(ip, port, cmd):
    try:
        device = connect_device(ip, port)
        if device is None:
            return {"ok": False, "output": None, "error": "Gerät nicht erreichbar"}
        output = device.shell(cmd)
        return {"ok": True, "output": output, "error": None}
    except Exception as exc:
        return {"ok": False, "output": None, "error": str(exc)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test dashboard.tests.test_adb_client -v 2`
Expected: all tests PASS (8 tests, OK).

- [ ] **Step 5: Commit**

```bash
git add dashboard/adb_client.py dashboard/tests/test_adb_client.py
git commit -m "Add ppadb wrapper for connect/run/status"
```

---

### Task 6: Dashboard view (`GET /`)

**Files:**
- Modify: `dashboard/views.py`
- Create: `dashboard/templates/dashboard/index.html`
- Create: `dashboard/static/dashboard/style.css`
- Test: `dashboard/tests/test_views.py`

- [ ] **Step 1: Write the failing tests**

Create `dashboard/tests/test_views.py`:

```python
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    @patch("dashboard.views.adb_client.check_status", return_value=True)
    @patch("dashboard.views.config_store.load")
    def test_dashboard_lists_devices_with_commands_and_status(self, mock_load, mock_status):
        mock_load.return_value = {
            "devices": [
                {"id": "d1", "name": "Wohnzimmer", "ip": "192.168.1.50", "port": 5555, "command_ids": ["c1"]},
            ],
            "commands": [
                {"id": "c1", "name": "Netflix öffnen", "cmd": "echo netflix"},
            ],
        }

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wohnzimmer")
        self.assertContains(response, "Netflix öffnen")
        self.assertContains(response, "Online")

    @patch("dashboard.views.adb_client.check_status", return_value=False)
    @patch("dashboard.views.config_store.load")
    def test_dashboard_shows_offline_status(self, mock_load, mock_status):
        mock_load.return_value = {
            "devices": [
                {"id": "d1", "name": "Wohnzimmer", "ip": "192.168.1.50", "port": 5555, "command_ids": []},
            ],
            "commands": [],
        }

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Offline")

    @patch("dashboard.views.adb_client.check_status", return_value=True)
    @patch("dashboard.views.config_store.load")
    def test_dashboard_shows_empty_state_without_devices(self, mock_load, mock_status):
        mock_load.return_value = {"devices": [], "commands": []}

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Keine Geräte konfiguriert")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: FAIL — `NoReverseMatch` or `AttributeError`, since `views.dashboard`
and the URL don't exist yet.

- [ ] **Step 3: Implement the view in `dashboard/views.py`**

```python
from django.shortcuts import render

from . import adb_client, config_store


def dashboard(request):
    data = config_store.load()
    command_map = {c["id"]: c for c in data["commands"]}
    devices = []
    for device in data["devices"]:
        commands = [command_map[cid] for cid in device["command_ids"] if cid in command_map]
        online = adb_client.check_status(device["ip"], device["port"])
        devices.append({**device, "commands": commands, "online": online})
    return render(request, "dashboard/index.html", {"devices": devices})
```

- [ ] **Step 4: Add the URL** (already added in Task 3, verify
`dashboard/urls.py` contains the `path("", views.dashboard, name="dashboard")`
entry from Task 3 Step 4 — no change needed here.)

- [ ] **Step 5: Create `dashboard/static/dashboard/style.css`**

```css
body {
  font-family: system-ui, sans-serif;
  margin: 2rem;
  background: #101418;
  color: #e8ecef;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

a {
  color: #6cb8ff;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

.device-card {
  background: #1b2229;
  border-radius: 8px;
  padding: 1rem;
}

.status {
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  margin-left: 0.5rem;
}

.status-online {
  background: #1f6e3a;
}

.status-offline {
  background: #7a2323;
}

.device-address {
  color: #9aa4ad;
  font-size: 0.85rem;
}

.command-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.75rem 0;
}

.command-button {
  background: #2a3540;
  color: #e8ecef;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
}

.command-button:hover {
  background: #35424f;
}

.result {
  font-size: 0.85rem;
  min-height: 1.2rem;
  color: #9aa4ad;
}
```

- [ ] **Step 6: Create `dashboard/templates/dashboard/index.html`**

```html
{% load static %}
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>AndroidTV Dashboard</title>
  <link rel="stylesheet" href="{% static 'dashboard/style.css' %}">
</head>
<body>
  <header>
    <h1>AndroidTV Dashboard</h1>
    <a href="{% url 'config' %}">Konfiguration</a>
  </header>

  <main class="device-grid">
    {% for device in devices %}
      <section class="device-card" data-device-id="{{ device.id }}">
        <h2>
          {{ device.name }}
          {% if device.online %}
            <span class="status status-online">Online</span>
          {% else %}
            <span class="status status-offline">Offline</span>
          {% endif %}
        </h2>
        <p class="device-address">{{ device.ip }}:{{ device.port }}</p>
        <div class="command-buttons">
          {% for command in device.commands %}
            <button
              type="button"
              class="command-button"
              data-device-id="{{ device.id }}"
              data-command-id="{{ command.id }}">
              {{ command.name }}
            </button>
          {% empty %}
            <p class="empty">Keine Commands zugewiesen.</p>
          {% endfor %}
        </div>
        <p class="result" data-result-for="{{ device.id }}"></p>
      </section>
    {% empty %}
      <p>Keine Geräte konfiguriert. <a href="{% url 'config' %}">Jetzt anlegen</a>.</p>
    {% endfor %}
  </main>

  {% csrf_token %}
  <script>
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;

    document.querySelectorAll('.command-button').forEach(function (button) {
      button.addEventListener('click', function () {
        const deviceId = button.dataset.deviceId;
        const commandId = button.dataset.commandId;
        const resultEl = document.querySelector('[data-result-for="' + deviceId + '"]');
        resultEl.textContent = 'Wird gesendet…';

        fetch('/device/' + deviceId + '/run/' + commandId + '/', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
        })
          .then(function (response) { return response.json(); })
          .then(function (data) {
            resultEl.textContent = data.ok
              ? 'OK: ' + (data.output || '')
              : 'Fehler: ' + data.error;
          })
          .catch(function () {
            resultEl.textContent = 'Fehler: Anfrage fehlgeschlagen';
          });
      });
    });
  </script>
</body>
</html>
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: 3 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add dashboard/views.py dashboard/templates dashboard/static dashboard/tests/test_views.py
git commit -m "Add dashboard view with online status and command buttons"
```

---

### Task 7: Run-command view (`POST /device/<id>/run/<id>/`)

**Files:**
- Modify: `dashboard/views.py`
- Modify: `dashboard/tests/test_views.py`

- [ ] **Step 1: Add the failing tests**

Append to `dashboard/tests/test_views.py`:

```python
class RunCommandViewTests(TestCase):
    @patch("dashboard.views.adb_client.run_command")
    @patch("dashboard.views.config_store.get_command")
    @patch("dashboard.views.config_store.get_device")
    def test_run_command_success(self, mock_get_device, mock_get_command, mock_run_command):
        mock_get_device.return_value = {"id": "d1", "ip": "192.168.1.50", "port": 5555}
        mock_get_command.return_value = {"id": "c1", "cmd": "echo netflix"}
        mock_run_command.return_value = {"ok": True, "output": "netflix\n", "error": None}

        response = self.client.post(reverse("run_command", args=["d1", "c1"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "output": "netflix\n", "error": None})
        mock_run_command.assert_called_once_with("192.168.1.50", 5555, "echo netflix")

    @patch("dashboard.views.config_store.get_command")
    @patch("dashboard.views.config_store.get_device")
    def test_run_command_unknown_device_returns_404(self, mock_get_device, mock_get_command):
        mock_get_device.return_value = None
        mock_get_command.return_value = {"id": "c1", "cmd": "echo netflix"}

        response = self.client.post(reverse("run_command", args=["d1", "c1"]))

        self.assertEqual(response.status_code, 404)

    def test_run_command_rejects_get(self):
        response = self.client.get(reverse("run_command", args=["d1", "c1"]))
        self.assertEqual(response.status_code, 405)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: FAIL — `views.run_command` doesn't exist yet.

- [ ] **Step 3: Implement the view**

Add to `dashboard/views.py`:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
```

(merge with the existing `from django.shortcuts import render` import line
into a single `django.shortcuts` import and add these two new imports above
it), then add:

```python
@require_POST
def run_command(request, device_id, command_id):
    device = config_store.get_device(device_id)
    command = config_store.get_command(command_id)
    if device is None or command is None:
        return JsonResponse({"ok": False, "error": "Unbekanntes Gerät oder Command"}, status=404)
    result = adb_client.run_command(device["ip"], device["port"], command["cmd"])
    return JsonResponse(result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: all tests PASS (6 tests, OK).

- [ ] **Step 5: Commit**

```bash
git add dashboard/views.py dashboard/tests/test_views.py
git commit -m "Add run_command endpoint"
```

---

### Task 8: Config view (`GET/POST /config/`)

**Files:**
- Modify: `dashboard/views.py`
- Create: `dashboard/templates/dashboard/config.html`
- Modify: `dashboard/tests/test_views.py`

- [ ] **Step 1: Add the failing tests**

Append to `dashboard/tests/test_views.py`:

```python
class ConfigViewTests(TestCase):
    @patch("dashboard.views.config_store.load")
    def test_config_page_lists_devices_and_commands(self, mock_load):
        mock_load.return_value = {
            "devices": [{"id": "d1", "name": "Wohnzimmer", "ip": "192.168.1.50", "port": 5555, "command_ids": []}],
            "commands": [{"id": "c1", "name": "Netflix öffnen", "cmd": "echo netflix"}],
        }

        response = self.client.get(reverse("config"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wohnzimmer")
        self.assertContains(response, "Netflix öffnen")

    @patch("dashboard.views.config_store.add_device")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_add_device_redirects(self, mock_load, mock_add_device):
        response = self.client.post(reverse("config"), {
            "action": "add_device",
            "name": "Wohnzimmer",
            "ip": "192.168.1.50",
            "port": "5555",
        })

        self.assertRedirects(response, reverse("config"))
        mock_add_device.assert_called_once_with("Wohnzimmer", "192.168.1.50", 5555)

    @patch("dashboard.views.config_store.update_device")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_update_device_redirects(self, mock_load, mock_update_device):
        response = self.client.post(reverse("config"), {
            "action": "update_device",
            "device_id": "d1",
            "name": "Schlafzimmer",
            "ip": "192.168.1.51",
            "port": "5556",
        })

        self.assertRedirects(response, reverse("config"))
        mock_update_device.assert_called_once_with("d1", "Schlafzimmer", "192.168.1.51", 5556)

    @patch("dashboard.views.config_store.delete_device")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_delete_device_redirects(self, mock_load, mock_delete_device):
        response = self.client.post(reverse("config"), {
            "action": "delete_device",
            "device_id": "d1",
        })

        self.assertRedirects(response, reverse("config"))
        mock_delete_device.assert_called_once_with("d1")

    @patch("dashboard.views.config_store.add_command")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_add_command_redirects(self, mock_load, mock_add_command):
        response = self.client.post(reverse("config"), {
            "action": "add_command",
            "name": "Netflix öffnen",
            "cmd": "echo netflix",
        })

        self.assertRedirects(response, reverse("config"))
        mock_add_command.assert_called_once_with("Netflix öffnen", "echo netflix")

    @patch("dashboard.views.config_store.update_command")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_update_command_redirects(self, mock_load, mock_update_command):
        response = self.client.post(reverse("config"), {
            "action": "update_command",
            "command_id": "c1",
            "name": "YouTube öffnen",
            "cmd": "echo yt",
        })

        self.assertRedirects(response, reverse("config"))
        mock_update_command.assert_called_once_with("c1", "YouTube öffnen", "echo yt")

    @patch("dashboard.views.config_store.delete_command")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_delete_command_redirects(self, mock_load, mock_delete_command):
        response = self.client.post(reverse("config"), {
            "action": "delete_command",
            "command_id": "c1",
        })

        self.assertRedirects(response, reverse("config"))
        mock_delete_command.assert_called_once_with("c1")

    @patch("dashboard.views.config_store.assign_command")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_assign_command_redirects(self, mock_load, mock_assign):
        response = self.client.post(reverse("config"), {
            "action": "assign_command",
            "device_id": "d1",
            "command_id": "c1",
        })

        self.assertRedirects(response, reverse("config"))
        mock_assign.assert_called_once_with("d1", "c1")

    @patch("dashboard.views.config_store.unassign_command")
    @patch("dashboard.views.config_store.load", return_value={"devices": [], "commands": []})
    def test_config_post_unassign_command_redirects(self, mock_load, mock_unassign):
        response = self.client.post(reverse("config"), {
            "action": "unassign_command",
            "device_id": "d1",
            "command_id": "c1",
        })

        self.assertRedirects(response, reverse("config"))
        mock_unassign.assert_called_once_with("d1", "c1")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: FAIL — `views.config_view` doesn't exist yet.

- [ ] **Step 3: Implement the view**

Add to `dashboard/views.py`:

```python
from django.shortcuts import redirect, render
```

(merge into the existing `django.shortcuts` import so it reads
`from django.shortcuts import redirect, render`), then add:

```python
def config_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_device":
            config_store.add_device(
                request.POST.get("name", "").strip(),
                request.POST.get("ip", "").strip(),
                int(request.POST.get("port", 5555)),
            )
        elif action == "update_device":
            config_store.update_device(
                request.POST.get("device_id"),
                request.POST.get("name", "").strip(),
                request.POST.get("ip", "").strip(),
                int(request.POST.get("port", 5555)),
            )
        elif action == "delete_device":
            config_store.delete_device(request.POST.get("device_id"))
        elif action == "add_command":
            config_store.add_command(
                request.POST.get("name", "").strip(),
                request.POST.get("cmd", "").strip(),
            )
        elif action == "update_command":
            config_store.update_command(
                request.POST.get("command_id"),
                request.POST.get("name", "").strip(),
                request.POST.get("cmd", "").strip(),
            )
        elif action == "delete_command":
            config_store.delete_command(request.POST.get("command_id"))
        elif action == "assign_command":
            config_store.assign_command(
                request.POST.get("device_id"), request.POST.get("command_id")
            )
        elif action == "unassign_command":
            config_store.unassign_command(
                request.POST.get("device_id"), request.POST.get("command_id")
            )
        return redirect("config")

    data = config_store.load()
    return render(
        request,
        "dashboard/config.html",
        {"devices": data["devices"], "commands": data["commands"]},
    )
```

- [ ] **Step 4: Create `dashboard/templates/dashboard/config.html`**

```html
{% load static %}
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Konfiguration – AndroidTV Dashboard</title>
  <link rel="stylesheet" href="{% static 'dashboard/style.css' %}">
</head>
<body>
  <header>
    <h1>Konfiguration</h1>
    <a href="{% url 'dashboard' %}">Zurück zum Dashboard</a>
  </header>

  <main>
    <section>
      <h2>Geräte</h2>
      <ul>
        {% for device in devices %}
          <li>
            <form method="post" style="display:inline-flex; gap:0.5rem; align-items:center">
              {% csrf_token %}
              <input type="hidden" name="action" value="update_device">
              <input type="hidden" name="device_id" value="{{ device.id }}">
              <input type="text" name="name" value="{{ device.name }}" required>
              <input type="text" name="ip" value="{{ device.ip }}" required>
              <input type="number" name="port" value="{{ device.port }}" required>
              <button type="submit">Speichern</button>
            </form>
            <form method="post" style="display:inline">
              {% csrf_token %}
              <input type="hidden" name="action" value="delete_device">
              <input type="hidden" name="device_id" value="{{ device.id }}">
              <button type="submit">Löschen</button>
            </form>
            <details>
              <summary>Commands zuweisen</summary>
              {% for command in commands %}
                <form method="post" style="display:inline">
                  {% csrf_token %}
                  <input type="hidden" name="device_id" value="{{ device.id }}">
                  <input type="hidden" name="command_id" value="{{ command.id }}">
                  {% if command.id in device.command_ids %}
                    <input type="hidden" name="action" value="unassign_command">
                    <button type="submit">✓ {{ command.name }}</button>
                  {% else %}
                    <input type="hidden" name="action" value="assign_command">
                    <button type="submit">+ {{ command.name }}</button>
                  {% endif %}
                </form>
              {% endfor %}
            </details>
          </li>
        {% empty %}
          <li>Keine Geräte konfiguriert.</li>
        {% endfor %}
      </ul>

      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="add_device">
        <input type="text" name="name" placeholder="Name" required>
        <input type="text" name="ip" placeholder="IP-Adresse" required>
        <input type="number" name="port" placeholder="Port" value="5555" required>
        <button type="submit">Gerät hinzufügen</button>
      </form>
    </section>

    <section>
      <h2>Commands</h2>
      <ul>
        {% for command in commands %}
          <li>
            <form method="post" style="display:inline-flex; gap:0.5rem; align-items:center">
              {% csrf_token %}
              <input type="hidden" name="action" value="update_command">
              <input type="hidden" name="command_id" value="{{ command.id }}">
              <input type="text" name="name" value="{{ command.name }}" required>
              <input type="text" name="cmd" value="{{ command.cmd }}" required>
              <button type="submit">Speichern</button>
            </form>
            <form method="post" style="display:inline">
              {% csrf_token %}
              <input type="hidden" name="action" value="delete_command">
              <input type="hidden" name="command_id" value="{{ command.id }}">
              <button type="submit">Löschen</button>
            </form>
          </li>
        {% empty %}
          <li>Keine Commands konfiguriert.</li>
        {% endfor %}
      </ul>

      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="add_command">
        <input type="text" name="name" placeholder="Name" required>
        <input type="text" name="cmd" placeholder="adb shell Befehl" required>
        <button type="submit">Command hinzufügen</button>
      </form>
    </section>
  </main>
</body>
</html>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test dashboard.tests.test_views -v 2`
Expected: all tests PASS (14 tests, OK).

- [ ] **Step 6: Commit**

```bash
git add dashboard/views.py dashboard/templates/dashboard/config.html dashboard/tests/test_views.py
git commit -m "Add config page for device/command CRUD and assignment"
```

---

### Task 9: Full test suite check

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `python manage.py test`
Expected: all tests across `test_config_store`, `test_adb_client`, and
`test_views` PASS (28 tests, OK), no errors.

- [ ] **Step 2: Run `python manage.py check` once more**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

---

### Task 10: README and manual smoke test

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# ADB AndroidTV Dashboard

Django-Dashboard zum Senden von ADB-Shell-Befehlen an mehrere AndroidTV-Geräte
im lokalen Netzwerk.

## Setup (kein venv, alle Pakete projekt-lokal)

```bash
./setup.sh
python manage.py runserver
```

Danach:
- Dashboard: http://127.0.0.1:8000/
- Konfiguration: http://127.0.0.1:8000/config/

Geräte und Commands werden in `config.json` im Projektverzeichnis
gespeichert (wird beim ersten Speichern automatisch angelegt).

Voraussetzung: Ein laufender `adb`-Server auf dem Host (`adb start-server`),
erreichbar unter `127.0.0.1:5037`, sowie Netzwerkzugriff auf die
AndroidTV-Geräte (ADB-Debugging über Netzwerk muss auf den Geräten aktiviert
sein).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Add README with setup instructions"
```

- [ ] **Step 3: Manual smoke test (requires `adb` installed and a reachable AndroidTV device)**

1. Run `adb start-server` on the host.
2. Run `./setup.sh && python manage.py runserver`.
3. Open `http://127.0.0.1:8000/config/`, add a device with the AndroidTV's
   IP and port 5555, add a command (e.g. `input keyevent KEYCODE_HOME`),
   assign it to the device.
4. Open `http://127.0.0.1:8000/`, confirm the device card shows an
   Online/Offline badge and the assigned command as a button.
5. Click the command button, confirm the AndroidTV reacts and the dashboard
   shows an "OK" result message.
6. Note the outcome in the PR/commit description; this step is not part of
   the automated test suite.
