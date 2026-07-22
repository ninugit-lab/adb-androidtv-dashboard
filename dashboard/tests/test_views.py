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
