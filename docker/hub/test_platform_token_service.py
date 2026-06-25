"""Unit tests for platform token helper functions."""

from __future__ import annotations

import base64
import json
import os
import time
import unittest
from unittest.mock import MagicMock, patch

from platform_token_utils import (
    decode_jwt_exp,
    normalize_cpu,
    normalize_memory,
    refresh_access_token,
    token_is_expired,
)


def _make_jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode("utf-8").rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp}).encode("utf-8")
    ).decode("utf-8").rstrip("=")
    return f"{header}.{payload}.signature"


class PlatformTokenUtilsTests(unittest.TestCase):
    def test_decode_jwt_exp(self):
        exp = int(time.time()) + 3600
        token = _make_jwt(exp)
        self.assertEqual(decode_jwt_exp(token), float(exp))

    def test_token_is_expired(self):
        expired = _make_jwt(int(time.time()) - 60)
        valid = _make_jwt(int(time.time()) + 3600)
        self.assertTrue(token_is_expired(expired))
        self.assertFalse(token_is_expired(valid))


class MemoryNormalizationTests(unittest.TestCase):
    def test_normalize_memory_converts_kubernetes_units(self):
        self.assertEqual(normalize_memory("1Gi"), "1G")
        self.assertEqual(normalize_memory("512Mi"), "512M")
        self.assertEqual(normalize_memory("2G"), "2G")


class CpuNormalizationTests(unittest.TestCase):
    def test_normalize_cpu_converts_kubernetes_millicores(self):
        self.assertEqual(normalize_cpu("500m"), 0.5)
        self.assertEqual(normalize_cpu("1"), 1.0)
        self.assertEqual(normalize_cpu("1000m"), 1.0)


class RefreshAccessTokenTests(unittest.TestCase):
    @patch("platform_token_utils.requests.post")
    def test_refresh_access_token_returns_new_token(self, post_mock):
        new_token = _make_jwt(int(time.time()) + 3600)
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"access_token": new_token, "refresh_token": "new-refresh"}
        post_mock.return_value = response

        auth_state = {"refresh_token": "old-refresh", "access_token": _make_jwt(int(time.time()) - 60)}
        with patch.dict(
            os.environ,
            {"KEYCLOAK_CLIENT_ID": "client", "KEYCLOAK_CLIENT_SECRET": "secret"},
            clear=False,
        ):
            token = refresh_access_token(auth_state)

        self.assertEqual(token, new_token)
        self.assertEqual(auth_state["access_token"], new_token)
        self.assertEqual(auth_state["refresh_token"], "new-refresh")

    def test_refresh_access_token_without_refresh_token_returns_none(self):
        auth_state = {"access_token": _make_jwt(int(time.time()) - 60)}
        self.assertIsNone(refresh_access_token(auth_state))

    @patch("platform_token_utils.requests.post")
    def test_refresh_access_token_keycloak_failure_returns_none(self, post_mock):
        response = MagicMock()
        response.status_code = 400
        post_mock.return_value = response

        auth_state = {"refresh_token": "old-refresh"}
        with patch.dict(
            os.environ,
            {"KEYCLOAK_CLIENT_ID": "client", "KEYCLOAK_CLIENT_SECRET": "secret"},
            clear=False,
        ):
            self.assertIsNone(refresh_access_token(auth_state))


if __name__ == "__main__":
    unittest.main()
