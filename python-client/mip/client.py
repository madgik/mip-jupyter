import requests
import os
import json
import time
import base64
import socket
from urllib.parse import urlparse


DEFAULT_BASE_URLS = [
    "http://platform-backend:8080/services",
    "http://platform-backend-service:8080/services",
    "http://localhost:8080/services",
    "http://172.17.0.1:8080/services",
]


class PortalClient:
    def __init__(self, base_url=None, token=None, timeout=None, allow_redirects=None):
        """Create a low-level HTTP client for Platform Backend APIs.

        Args:
            base_url: Backend base URL, defaults to env PLATFORM_BACKEND_URL
                (or legacy PORTAL_BACKEND_URL). If neither is set, the client
                auto-discovers from known local endpoints.
            token: Bearer token. If missing, reads PLATFORM_TOKEN, PORTAL_TOKEN,
                or token file.
            timeout: Default request timeout in seconds. If not provided, reads
                env PLATFORM_BACKEND_TIMEOUT (default 30).
            allow_redirects: Whether to follow HTTP redirects. Defaults to False
                because redirects from API endpoints usually mean "login required"
                and can otherwise hang in environments without external network.
        """
        configured_url = base_url or os.getenv("PLATFORM_BACKEND_URL") or os.getenv("PORTAL_BACKEND_URL")
        self._auto_base_url = configured_url is None
        self._base_url_candidates = self._build_base_url_candidates(configured_url)
        self.base_url = self._base_url_candidates[0]
        self.token = token or os.getenv("PLATFORM_TOKEN") or os.getenv("PORTAL_TOKEN") or self._read_token_from_file()
        self.timeout = float(timeout if timeout is not None else os.getenv("PLATFORM_BACKEND_TIMEOUT", "30"))
        if allow_redirects is None:
            allow_redirects = os.getenv("PLATFORM_BACKEND_ALLOW_REDIRECTS", "0") in ("1", "true", "True")
        self.allow_redirects = bool(allow_redirects)
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})

    def _build_base_url_candidates(self, configured_url):
        """Return ordered unique base URL candidates."""
        if configured_url:
            return [configured_url.rstrip("/")]

        resolvable = []
        unresolved = []
        for url in DEFAULT_BASE_URLS:
            if self._url_host_resolves(url):
                resolvable.append(url)
            else:
                unresolved.append(url)
        ordered = resolvable + unresolved
        # Keep insertion order while removing duplicates.
        return list(dict.fromkeys(ordered))

    def _url_host_resolves(self, url):
        """Best-effort DNS check used only for ordering fallback candidates."""
        host = (urlparse(url).hostname or "").strip()
        if not host:
            return False
        try:
            socket.getaddrinfo(host, None)
            return True
        except OSError:
            return False

    def _maybe_refresh_token_via_jupyterhub(self):
        """Refresh access token via JupyterHub (if running inside a JupyterHub single-user server).

        We avoid baking Keycloak client secrets into notebooks. Instead, the hub owns the
        refresh token (auth_state) and can mint a fresh access token on demand.
        """
        api_url = os.getenv("JUPYTERHUB_API_URL", "").rstrip("/")
        api_token = os.getenv("JUPYTERHUB_API_TOKEN", "")
        if not api_url or not api_token:
            return False

        # This endpoint is provided by our JupyterHub config (see mip-deployment/*/jupyterhub*).
        url = f"{api_url}/portal-token"
        try:
            r = requests.get(
                url,
                headers={"Authorization": f"token {api_token}"},
                timeout=min(self.timeout, 15.0),
                allow_redirects=False,
            )
        except Exception:
            return False

        if r.status_code != 200:
            return False

        try:
            data = r.json() if r.content else {}
        except Exception:
            return False

        token = (data or {}).get("access_token")
        if not token or not isinstance(token, str):
            return False

        self.set_token(token)
        return True

    def _read_token_from_file(self):
        """Read token from local notebook workspace if available."""
        # Try both hidden and non-hidden (for Jupyter API compatibility).
        for filename in ['mip_token', '.mip_token']:
            try:
                with open(filename, 'r') as f:
                    return f.read().strip()
            except FileNotFoundError:
                continue
        return None
            
    def set_token(self, token):
        """Set or replace bearer token used in subsequent requests."""
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})

    def get(self, endpoint, params=None):
        """Execute a GET request and return parsed JSON."""
        self._raise_if_expired_token()
        response, url = self._request_with_base_url_failover("get", endpoint, params=params)
        self._raise_if_redirected(response, url)
        response.raise_for_status()
        return self._json_or_empty(response)

    def post(self, endpoint, data=None):
        """Execute a POST request with JSON body and return parsed JSON."""
        self._raise_if_expired_token()
        response, url = self._request_with_base_url_failover("post", endpoint, json=data)
        self._raise_if_redirected(response, url)
        response.raise_for_status()
        return self._json_or_empty(response)

    def _request_with_base_url_failover(self, method, endpoint, **kwargs):
        """Execute request and fall back across known base URLs when DNS/connection fails.

        Failover is enabled only when no explicit base_url/env URL was provided.
        """
        candidates = self._base_url_candidates if self._auto_base_url else [self.base_url]
        last_exc = None

        for index, candidate in enumerate(candidates):
            url = f"{candidate}{endpoint}"
            try:
                request_fn = getattr(self.session, method)
                response = request_fn(
                    url,
                    timeout=self.timeout,
                    allow_redirects=self.allow_redirects,
                    **kwargs,
                )
                # If the hub-injected access token expired, attempt a one-time refresh via hub and retry.
                if response.status_code == 401 and self._maybe_refresh_token_via_jupyterhub():
                    response = request_fn(
                        url,
                        timeout=self.timeout,
                        allow_redirects=self.allow_redirects,
                        **kwargs,
                    )
                # Persist working endpoint for subsequent calls.
                self.base_url = candidate
                if self._auto_base_url and index > 0:
                    remaining = [x for x in self._base_url_candidates if x != candidate]
                    self._base_url_candidates = [candidate] + remaining
                return response, url
            except requests.exceptions.ConnectionError as exc:
                last_exc = exc
                if not self._should_try_next_candidate(exc, index, len(candidates)):
                    raise

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Request failed without response.")

    def _should_try_next_candidate(self, exc, index, total_candidates):
        if not self._auto_base_url:
            return False
        if index >= total_candidates - 1:
            return False
        message = str(exc).lower()
        transient_connection_markers = (
            "name resolution",
            "failed to resolve",
            "nameresolutionerror",
            "newconnectionerror",
            "connection refused",
            "max retries exceeded",
        )
        return any(marker in message for marker in transient_connection_markers)

    def _raise_if_redirected(self, response, url):
        """Fail fast on HTTP redirects from API endpoints (usually auth/login)."""
        status = getattr(response, "status_code", None)
        if not isinstance(status, int) or status < 300 or status >= 400:
            return
        location = None
        try:
            location = (response.headers or {}).get("Location")
        except Exception:
            location = None
        raise RuntimeError(
            "Platform Backend request was redirected (likely authentication required).\n"
            f"- request: {url}\n"
            f"- status: {status}\n"
            f"- location: {location}\n\n"
            "Fix:\n"
            "- If you run this OUTSIDE docker-compose: use configure(base_url='http://localhost:8080/services').\n"
            "- If authentication is enabled: pass a bearer token via configure(token=...), or set PLATFORM_TOKEN.\n"
        )

    def _json_or_empty(self, response):
        """Return parsed JSON, tolerating empty/whitespace-only successful bodies."""
        status = getattr(response, "status_code", None)
        if status == 204:
            return {}

        # Prefer JSON parsing when Content-Type indicates JSON, without relying on response.text
        # (makes unit tests with mocks more robust, and avoids surprise decoding issues).
        content_type = ""
        try:
            content_type = (response.headers.get("Content-Type") or "").lower()
        except Exception:
            content_type = ""
        if "json" in content_type:
            return response.json()

        text = getattr(response, "text", "") or ""
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                text = ""
        if not text.strip():
            return {}
        try:
            return response.json()
        except Exception as exc:
            lower_preview = text[:200].lower()
            if "<!doctype html" in lower_preview or "<html" in lower_preview:
                raise RuntimeError(
                    "Backend returned HTML instead of JSON. This usually means the backend is "
                    "sending a login page (authentication required) or you hit the wrong base_url.\n\n"
                    "Fix:\n"
                    "- If you run this OUTSIDE docker-compose: use configure(base_url='http://localhost:8080/services').\n"
                    "- If authentication is enabled: pass a bearer token via configure(token=...), or set PLATFORM_TOKEN.\n"
                ) from exc
            raise RuntimeError(
                f"Backend returned non-JSON response (Content-Type: {content_type or 'unknown'})."
            ) from exc

    def _raise_if_expired_token(self):
        """Raise a clear error when a JWT token exists but is expired."""
        if not self.token:
            return
        payload = self._decode_jwt_payload(self.token)
        if not payload:
            return
        exp = payload.get("exp")
        if isinstance(exp, (int, float)) and exp <= time.time():
            # Best-effort refresh when running inside JupyterHub.
            if self._maybe_refresh_token_via_jupyterhub():
                return
            raise RuntimeError(
                "The API token is expired and could not be refreshed automatically.\n\n"
                "Fix:\n"
                "- If you are in JupyterHub: re-login or restart your notebook server session.\n"
                "- Otherwise: provide a fresh token via configure(token=...) or set PLATFORM_TOKEN.\n"
            )

    def _decode_jwt_payload(self, token):
        """Best-effort JWT payload decode, returns {} for non-JWT inputs."""
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            return json.loads(decoded.decode("utf-8"))
        except Exception:
            return {}

    def delete(self, endpoint):
        """Execute a DELETE request and return the raw response object."""
        response, url = self._request_with_base_url_failover("delete", endpoint)
        self._raise_if_redirected(response, url)
        response.raise_for_status()
        return response

# Singleton instance to be used by other modules
_client_instance = None

def get_client():
    """Get the singleton configured client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = PortalClient()
    return _client_instance

def configure(base_url=None, token=None):
    """Configure (or reconfigure) the global client singleton.

    Typical notebook usage:
        from mip import configure
        configure()
    """
    global _client_instance
    _client_instance = PortalClient(base_url, token)
