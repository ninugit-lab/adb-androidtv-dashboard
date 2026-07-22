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
