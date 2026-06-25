"""JupyterHub API handler that returns or refreshes the platform-backend OAuth token."""

from __future__ import annotations

from jupyterhub import orm
from jupyterhub.apihandlers.base import APIHandler
from tornado import web

from platform_token_utils import refresh_access_token, token_is_expired


class PlatformTokenHandler(APIHandler):
    """Return the platform-backend Bearer token for the authenticated user server.

    Uses APIHandler (in-process token auth) instead of HubAuthenticated because this
    endpoint is registered on the hub itself; HubAuthenticated would HTTP-call the
    hub API and deadlock the single-threaded event loop.
    """

    async def get(self) -> None:
        user = self.current_user
        if user is None:
            raise web.HTTPError(403, "Not authenticated")
        if isinstance(user, orm.Service):
            raise web.HTTPError(403, "Only user server tokens are supported")

        auth_state = await user.get_auth_state() or {}
        access_token = auth_state.get("access_token")
        if access_token and token_is_expired(access_token):
            refreshed = refresh_access_token(auth_state)
            if refreshed:
                access_token = refreshed
                await user.save_auth_state(auth_state)

        if not access_token:
            raise web.HTTPError(401, "No platform access token available")

        if token_is_expired(access_token):
            raise web.HTTPError(
                401,
                "Platform access token is expired and could not be refreshed. Re-login to JupyterHub.",
            )

        self.set_header("Content-Type", "application/json")
        self.write({"access_token": access_token})
