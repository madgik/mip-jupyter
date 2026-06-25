import os

from platform_token_service import PlatformTokenHandler
from platform_token_utils import normalize_cpu, normalize_memory, refresh_access_token, token_is_expired


QWEN_CODEX_MODEL = "qwen36-nvfp4"


def _env(name, default=""):
    return os.environ.get(name, default)


def _env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_base_url(path):
    if not path:
        return "/notebook/"
    normalized = path if path.startswith("/") else f"/{path}"
    if not normalized.endswith("/"):
        normalized += "/"
    return normalized


_notebook_base = _normalize_base_url(_env("JUPYTERHUB_BASE_PATH", "/notebook/")).rstrip("/")
# HubAuthenticated and other hub code read JUPYTERHUB_BASE_URL (not JUPYTERHUB_BASE_PATH).
os.environ.setdefault("JUPYTERHUB_BASE_URL", f"{_notebook_base}/")

# Served behind platform-ui nginx at /notebook/.
c.JupyterHub.bind_url = "http://:8000"
c.JupyterHub.base_url = f"{_notebook_base}/"
# hub_bind_url listens inside the hub pod; hub_connect_url is how servers reach the Hub API.
# Include base_url path — with base_url=/notebook/, the API is at /notebook/hub/api (not /hub/api).
_hub_api_host = _env("JUPYTERHUB_INTERNAL_HOST", "jupyterhub")
_hub_api_port = _env("JUPYTERHUB_HUB_API_PORT", "8081")
c.JupyterHub.hub_bind_url = f"http://:{_hub_api_port}"
c.JupyterHub.hub_connect_url = f"http://{_hub_api_host}:{_hub_api_port}{_notebook_base}/hub"
c.JupyterHub.tornado_settings = {
    "headers": {
        "Content-Security-Policy": "frame-ancestors 'self'",
    },
    # Allow platform-ui at /notebook to read _xsrf for Hub API calls.
    "xsrf_cookie_kwargs": {"path": f"{_notebook_base}/"},
}

# Session cookie behind platform-ui nginx / HTTPS reverse proxy.
_cookie_secure = _env_bool("JUPYTERHUB_COOKIE_SECURE", True)
c.JupyterHub.cookie_options = {
    "SameSite": "Lax",
    "Secure": _cookie_secure,
}

_keycloak_client_id = _env("KEYCLOAK_CLIENT_ID")
_use_keycloak = bool(_keycloak_client_id) and not _env_bool("JUPYTERHUB_USE_DUMMY_AUTH", False)

_crypt_key = _env("JUPYTERHUB_CRYPT_KEY")
if _crypt_key:
    c.CryptKeeper.keys = [_crypt_key]

if _use_keycloak:
    _auth_url = _env("KEYCLOAK_AUTH_URL", "https://iam.ebrains.eu/auth/").rstrip("/")
    _realm = _env("KEYCLOAK_REALM", "MIP")
    _realm_base = f"{_auth_url}/realms/{_realm}"

    c.JupyterHub.authenticator_class = "oauthenticator.generic.GenericOAuthenticator"
    c.GenericOAuthenticator.client_id = _keycloak_client_id
    c.GenericOAuthenticator.client_secret = _env("KEYCLOAK_CLIENT_SECRET")
    c.GenericOAuthenticator.authorize_url = f"{_realm_base}/protocol/openid-connect/auth"
    c.GenericOAuthenticator.token_url = f"{_realm_base}/protocol/openid-connect/token"
    c.GenericOAuthenticator.userdata_url = f"{_realm_base}/protocol/openid-connect/userinfo"
    c.GenericOAuthenticator.username_claim = "preferred_username"
    c.GenericOAuthenticator.scope = ["openid", "profile", "email", "offline_access"]
    c.GenericOAuthenticator.allow_all = True
    c.GenericOAuthenticator.manage_groups = False
    c.GenericOAuthenticator.auto_login = _env_bool("JUPYTERHUB_AUTO_LOGIN", True)
    if _env_bool("JUPYTERHUB_OAUTH_PROMPT_NONE", False):
        c.GenericOAuthenticator.extra_authorize_params = {"prompt": "none"}
    c.GenericOAuthenticator.logout_redirect_url = _env(
        "JUPYTERHUB_LOGOUT_REDIRECT_URL", "/"
    )
else:
    c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"
    c.DummyAuthenticator.password = _env("JUPYTERHUB_DUMMY_PASSWORD", "")

c.Authenticator.enable_auth_state = True

c.JupyterHub.spawner_class = "kubespawner.KubeSpawner"
c.KubeSpawner.image = _env("JUPYTER_SINGLEUSER_IMAGE", "hbpmip/mip-jupyter:dev")
c.KubeSpawner.image_pull_policy = _env("JUPYTER_IMAGE_PULL_POLICY", "Always")
c.KubeSpawner.namespace = _env("JUPYTERHUB_NAMESPACE", os.environ.get("POD_NAMESPACE", "default"))

# Pass platform backend URL to all spawned notebooks.
_spawner_env = {
    "PLATFORM_BACKEND_URL": _env(
        "PLATFORM_BACKEND_URL", "http://platform-backend-service:8080/services"
    ),
    "JUPYTER_TOKEN": _env("JUPYTER_SINGLEUSER_TOKEN", ""),
    "JUPYTERHUB_API_URL": f"http://{_hub_api_host}:{_hub_api_port}{_notebook_base}/hub/api",
}
_codex_base_url = _env("CODEX_VLLM_BASE_URL")
if _codex_base_url:
    _spawner_env["CODEX_VLLM_BASE_URL"] = _codex_base_url
    _spawner_env["CODEX_VLLM_MODEL"] = QWEN_CODEX_MODEL
    _codex_provider = _env("CODEX_VLLM_PROVIDER")
    if _codex_provider:
        _spawner_env["CODEX_VLLM_PROVIDER"] = _codex_provider
c.KubeSpawner.environment = _spawner_env

# Persistence configuration.
c.KubeSpawner.storage_class = _env("JUPYTER_STORAGE_CLASS", "k8s-local-storage")
c.KubeSpawner.storage_capacity = _env("JUPYTER_STORAGE_CAPACITY", "2Gi")

# Resource limits for spawned notebooks.
c.KubeSpawner.cpu_limit = normalize_cpu(_env("JUPYTER_CPU_LIMIT", "1"))
c.KubeSpawner.mem_limit = normalize_memory(_env("JUPYTER_MEM_LIMIT", "1G"))
c.KubeSpawner.cpu_guarantee = normalize_cpu(_env("JUPYTER_CPU_GUARANTEE", "500m"))
c.KubeSpawner.mem_guarantee = normalize_memory(_env("JUPYTER_MEM_GUARANTEE", "512M"))

# Security: ensure pods run as the jovyan user.
c.KubeSpawner.pod_security_context = {
    "fsGroup": 100,
    "runAsUser": 1000,
}


async def inject_platform_token(spawner):
    """Inject platform-backend Bearer token into the single-user server environment."""
    auth_state = await spawner.user.get_auth_state() or {}
    token = auth_state.get("access_token")
    if token and token_is_expired(token):
        refreshed = refresh_access_token(auth_state)
        if refreshed:
            token = refreshed
            await spawner.user.save_auth_state(auth_state)
    if not token:
        token = _env("MIP_TOKEN") or _env("PLATFORM_TOKEN")
    if token:
        spawner.environment["MIP_TOKEN"] = token


c.Spawner.pre_spawn_hook = inject_platform_token

c.JupyterHub.extra_handlers = [
    (r"/api/platform-token", PlatformTokenHandler),
]
