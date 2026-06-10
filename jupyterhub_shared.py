"""Shared helpers for deployment-specific JupyterHub configuration."""

from __future__ import annotations

import os


DEFAULT_OAUTH_SCOPE = ("openid", "profile", "email", "offline_access")


def bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def build_keycloak_urls(auth_url, realm):
    base = (auth_url or "").rstrip("/")
    return {
        "authorize_url": f"{base}/realms/{realm}/protocol/openid-connect/auth",
        "token_url": f"{base}/realms/{realm}/protocol/openid-connect/token",
        "userdata_url": f"{base}/realms/{realm}/protocol/openid-connect/userinfo",
    }


def configure_generic_oauth(
    c,
    *,
    auth_url,
    realm,
    client_id,
    client_secret,
    callback_url,
    scope=DEFAULT_OAUTH_SCOPE,
):
    urls = build_keycloak_urls(auth_url, realm)

    c.JupyterHub.authenticator_class = "generic-oauth"
    c.Authenticator.enable_auth_state = True
    c.Authenticator.refresh_pre_spawn = True

    c.GenericOAuthenticator.login_service = "Keycloak"
    c.GenericOAuthenticator.client_id = client_id
    c.GenericOAuthenticator.client_secret = client_secret
    c.GenericOAuthenticator.authorize_url = urls["authorize_url"]
    c.GenericOAuthenticator.token_url = urls["token_url"]
    c.GenericOAuthenticator.userdata_url = urls["userdata_url"]
    c.GenericOAuthenticator.username_claim = "preferred_username"
    c.GenericOAuthenticator.username_key = "preferred_username"
    c.GenericOAuthenticator.oauth_callback_url = callback_url
    c.GenericOAuthenticator.scope = list(scope)
    c.GenericOAuthenticator.allow_all = True
    c.GenericOAuthenticator.auto_login = True


def configure_dummy_auth(c, *, password=""):
    c.JupyterHub.authenticator_class = "dummy"
    c.Authenticator.auto_login = False
    if password:
        c.DummyAuthenticator.password = password


def extract_access_token(auth_state):
    if not auth_state:
        return None
    return auth_state.get("access_token") or (auth_state.get("token_response") or {}).get("access_token")


def build_singleuser_csp_arg(frame_ancestors):
    return (
        '--ServerApp.tornado_settings='
        f'{{"headers":{{"Content-Security-Policy":"frame-ancestors {frame_ancestors}"}}}}'
    )


def install_platform_token_handler(c, *, authentication_enabled):
    from jupyterhub.apihandlers.base import APIHandler
    from tornado import web

    class PlatformTokenHandler(APIHandler):
        @web.authenticated
        async def get(self):
            if not authentication_enabled:
                raise web.HTTPError(404, "Token refresh endpoint is disabled when AUTHENTICATION=0")

            user = self.current_user
            if not user:
                raise web.HTTPError(401)

            auth_model = await self.authenticator.refresh_user(user, handler=self)
            if auth_model is False:
                raise web.HTTPError(401, "Authentication expired; please login again")
            if isinstance(auth_model, dict):
                await user.save_auth_state(auth_model.get("auth_state") or {})

            auth_state = await user.get_auth_state() or {}
            token = extract_access_token(auth_state)
            if not token:
                raise web.HTTPError(404, "No access_token in auth_state")

            self.finish({"access_token": token})

    c.JupyterHub.extra_handlers = [(r"/api/platform-token", PlatformTokenHandler)]
