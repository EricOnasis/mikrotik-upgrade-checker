import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checker import compare_versions, fetch_installed_version, fetch_latest_version


class CompareVersionsTests(unittest.TestCase):
    def test_older_is_less(self):
        self.assertEqual(compare_versions("7.14.2", "7.15.3"), -1)

    def test_equal(self):
        self.assertEqual(compare_versions("7.15.3", "7.15.3"), 0)

    def test_newer_is_greater(self):
        self.assertEqual(compare_versions("7.16.0", "7.15.3"), 1)

    def test_different_segment_counts(self):
        self.assertEqual(compare_versions("7.15", "7.15.0"), 0)
        self.assertEqual(compare_versions("7.15.1", "7.15"), 1)


class FetchInstalledVersionTests(unittest.TestCase):
    ROUTER = {"name": "r1", "host": "10.0.0.1", "username": "admin", "password": "x"}

    @patch("checker.paramiko.SSHClient")
    def test_parses_version_from_resource_print(self, mock_ssh):
        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"uptime: 3w2d\nversion: 7.14.2 (stable)\n"
        client.exec_command.return_value = (MagicMock(), stdout, MagicMock())
        mock_ssh.return_value = client

        version = fetch_installed_version(self.ROUTER)
        self.assertEqual(version, "7.14.2")

    @patch("checker.paramiko.SSHClient")
    def test_unparseable_output_raises(self, mock_ssh):
        client = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"garbage output"
        client.exec_command.return_value = (MagicMock(), stdout, MagicMock())
        mock_ssh.return_value = client

        with self.assertRaises(RuntimeError):
            fetch_installed_version(self.ROUTER)

    @patch("checker.paramiko.SSHClient")
    def test_connection_error_raises_runtime_error(self, mock_ssh):
        client = MagicMock()
        client.connect.side_effect = OSError("unreachable")
        mock_ssh.return_value = client

        with self.assertRaises(RuntimeError):
            fetch_installed_version(self.ROUTER)


class FetchLatestVersionTests(unittest.TestCase):
    @patch("checker.request.urlopen")
    def test_parses_version_from_response(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = b"7.15.3 1700000000"
        response.__enter__.return_value = response
        mock_urlopen.return_value = response

        self.assertEqual(fetch_latest_version(), "7.15.3")

    @patch("checker.request.urlopen")
    def test_empty_response_raises(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = b""
        response.__enter__.return_value = response
        mock_urlopen.return_value = response

        with self.assertRaises(RuntimeError):
            fetch_latest_version()


if __name__ == "__main__":
    unittest.main()
