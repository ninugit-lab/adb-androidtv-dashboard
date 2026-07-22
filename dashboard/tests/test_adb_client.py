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
