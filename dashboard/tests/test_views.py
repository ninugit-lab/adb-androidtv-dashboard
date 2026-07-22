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
