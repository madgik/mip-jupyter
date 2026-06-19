import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from mip import Client
from mip.exceptions import MipBackendError
from mip.exceptions import MipConfigurationError
from mip.transport import Transport


class TestClient(unittest.TestCase):
    def test_from_env_reads_mip_environment(self):
        with patch.dict(os.environ, {"MIP_BASE_URL": "http://backend/services", "MIP_TOKEN": "token"}, clear=True):
            client = Client.from_env()
        self.assertEqual(client._transport.base_url, "http://backend/services/")
        self.assertEqual(client._transport.token, "token")

    def test_from_env_reads_mip_token_with_platform_backend_url(self):
        with patch.dict(
            os.environ,
            {"PLATFORM_BACKEND_URL": "http://backend/services", "MIP_TOKEN": "mip-token"},
            clear=True,
        ):
            client = Client.from_env()
        self.assertEqual(client._transport.base_url, "http://backend/services/")
        self.assertEqual(client._transport.token, "mip-token")

    def test_from_env_prefers_platform_backend_url(self):
        with patch.dict(
            os.environ,
            {
                "PLATFORM_BACKEND_URL": "http://platform/services",
                "MIP_BASE_URL": "http://mip/services",
                "PLATFORM_TOKEN": "platform-token",
            },
            clear=True,
        ):
            client = Client.from_env()
        self.assertEqual(client._transport.base_url, "http://platform/services/")
        self.assertEqual(client._transport.token, "platform-token")

    def test_from_env_requires_base_url(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MipConfigurationError):
                Client.from_env()

    def test_client_does_not_expose_http_methods(self):
        client = Client("http://backend/services")
        self.assertFalse(hasattr(client, "get"))
        self.assertFalse(hasattr(client, "post"))

    def test_experiment_registry_maps_public_methods_to_backend_endpoints(self):
        client = Client("http://backend/services")
        transport = MagicMock()
        client._transport = transport
        transport.get.side_effect = [
            {"items": [{"id": "exp-1"}]},
            {"id": "exp-1", "status": "success"},
        ]

        registry = client.experiments()

        self.assertEqual(registry.list(), [{"id": "exp-1"}])
        self.assertEqual(registry.get("exp-1"), {"id": "exp-1", "status": "success"})
        self.assertIsNone(registry.delete("exp-1"))
        transport.get.assert_any_call("/experiments")
        transport.get.assert_any_call("/experiments/exp-1")
        transport.delete.assert_called_once_with("/experiments/exp-1")


class TestTransport(unittest.TestCase):
    @patch("mip.transport.requests.Session")
    def test_get_joins_base_url_and_returns_json(self, session_cls):
        response = MagicMock()
        response.status_code = 200
        response.content = b'{"ok": true}'
        response.json.return_value = {"ok": True}
        session = session_cls.return_value
        session.request.return_value = response

        transport = Transport("http://backend/services", token="token")
        payload = transport.get("/data-models", params={"q": "x"})

        self.assertEqual(payload, {"ok": True})
        session.headers.update.assert_called_with({"Authorization": "Bearer token"})
        session.request.assert_called_with(
            "GET",
            "http://backend/services/data-models",
            timeout=30.0,
            allow_redirects=False,
            params={"q": "x"},
        )

    @patch("mip.transport.requests.Session")
    def test_backend_error_is_wrapped(self, session_cls):
        response = MagicMock()
        response.status_code = 500
        response.text = "boom"
        response.json.side_effect = ValueError("not json")
        response.headers = {}
        session_cls.return_value.request.return_value = response

        transport = Transport("http://backend/services")
        with self.assertRaises(MipBackendError):
            transport.get("/data-models")


if __name__ == "__main__":
    unittest.main()
