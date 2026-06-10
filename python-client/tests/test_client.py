import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import requests

from mip import configure
from mip.client import PortalClient
from mip.errors import MipConfigurationError
from mip.client import get_client


class TestPortalClientConfiguration(unittest.TestCase):
    def test_get_client_requires_configure(self):
        import mip.client as client_module

        client_module._client_instance = None
        with self.assertRaises(MipConfigurationError):
            get_client()

    def test_configure_sets_singleton(self):
        configure(base_url="http://mock-backend", token="mock-token")
        client = get_client()
        self.assertEqual(client.base_url, "http://mock-backend")
        self.assertEqual(client.token, "mock-token")


class TestPortalClientBaseUrlResolution(unittest.TestCase):
    @patch("mip.client.socket.getaddrinfo")
    def test_prefers_localhost_when_compose_host_is_unresolvable(self, mock_getaddrinfo):
        def side_effect(host, _port):
            if host in ("platform-backend", "platform-backend-service"):
                raise OSError("unresolvable")
            return [(None, None, None, None, None)]

        mock_getaddrinfo.side_effect = side_effect
        client = PortalClient(token="mock-token")
        self.assertEqual(client.base_url, "http://localhost:8080/services")

    @patch("mip.client.requests.Session.get")
    @patch("mip.client.socket.getaddrinfo")
    def test_falls_back_to_next_candidate_on_connection_error(self, mock_getaddrinfo, mock_get):
        def resolve_side_effect(host, _port):
            if host == "platform-backend-service":
                raise OSError("unresolvable")
            return [(None, None, None, None, None)]

        mock_getaddrinfo.side_effect = resolve_side_effect

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"experiments":[]}'
        mock_response.json.return_value = {"experiments": []}
        mock_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.exceptions.ConnectionError(
                "Failed to resolve 'platform-backend' (NameResolutionError)"
            ),
            mock_response,
        ]

        client = PortalClient(token="mock-token")
        payload = client.get("/experiments", params={"size": 10, "page": 0})

        self.assertEqual(payload, {"experiments": []})
        self.assertEqual(client.base_url, "http://localhost:8080/services")


if __name__ == "__main__":
    unittest.main()
