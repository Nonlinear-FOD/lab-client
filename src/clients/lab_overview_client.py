from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from .auth_manager import AuthError, LabAuthManager
from .base_client import _auth_disabled


class LabOverviewClient:
    """Read-only client for overview and system endpoints. Can be used to see what devices are
    connected and which are currently used.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        user: Optional user name for lock-aware endpoints (passed as `X-User`).
    """

    def __init__(
        self,
        base_url: str,
        user: str | None = None,
        auth: LabAuthManager | None = None,
        token_path: str | Path | None = None,
        interactive_auth: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self._auth = None
        if not _auth_disabled():
            self._auth = auth or LabAuthManager(
                self.base_url,
                token_path=token_path,
                interactive=interactive_auth,
            )
            if self.user is None:
                self.user = self._auth.user_login()

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.user:
            headers["X-User"] = self.user
        if self._auth:
            try:
                headers["Authorization"] = self._auth.authorization_header()
                if "X-User" not in headers:
                    login = self._auth.user_login()
                    if login:
                        headers["X-User"] = login
                        self.user = login
            except AuthError as exc:
                raise RuntimeError(
                    f"Authentication with {self.base_url} failed: {exc}"
                ) from exc
        return headers

    def _json_or_raise(self, resp: requests.Response) -> dict[str, Any]:
        resp.raise_for_status()
        return resp.json()

    def devices(self) -> dict[str, Any]:
        """Return connection/lock status for all configured devices.

        Returns:
            Mapping of device name to `{"connected": bool, "connected_since": str|None, "used_by": str|None}`.
        """
        url = f"{self.base_url}/overview/devices"
        resp = self._perform_request("GET", url)
        return self._json_or_raise(resp)

    def list_used_instruments(self) -> dict[str, Any]:
        """Return current locks: which user holds which device (if any)."""
        url = f"{self.base_url}/overview/locks"
        resp = self._perform_request("GET", url)
        return self._json_or_raise(resp)

    def list_connected_instruments(self) -> dict[str, Any]:
        """Enumerate VISA resources on the server host (no probing)."""
        url = f"{self.base_url}/system/resources"
        resp = self._perform_request("GET", url)
        return self._json_or_raise(resp)

    def _perform_request(
        self, method: str, url: str, **kwargs: Any
    ) -> requests.Response:
        base_payload = dict(kwargs)
        timeout = base_payload.pop("timeout", None)
        attempts = 0
        while True:
            payload = dict(base_payload)
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=timeout,
                    **payload,
                )
            except requests.exceptions.RequestException as exc:
                raise ConnectionError(
                    f"Could not reach {self.base_url}: {exc}"
                ) from exc

            if resp.status_code == 401 and self._auth and attempts == 0:
                self._auth.reset_session()
                attempts += 1
                continue
            return resp


class LabSystemClient:
    """Helper focused on system-maintenance endpoints (/system/update, /client-docs/*) and
    session workers (list/restart/shutdown).

    Accepts either a pre-configured :class:`LabOverviewClient` (via ``overview_client``)
    or the same constructor arguments so it can manage its own instance.
    """

    def __init__(
        self,
        base_url: str | None = None,
        user: str | None = None,
        auth: LabAuthManager | None = None,
        token_path: str | Path | None = None,
        interactive_auth: bool = True,
    ) -> None:
        if base_url is None:
            raise ValueError(
                "base_url is required when overview_client is not provided"
            )
        self._client = LabOverviewClient(
            base_url,
            user=user,
            auth=auth,
            token_path=token_path,
            interactive_auth=interactive_auth,
        )

    @property
    def base_url(self) -> str:
        return self._client.base_url

    def sessions(self) -> dict[str, Any]:
        """Return metadata about all active per-user workers.

        Returns:
            JSON payload from `GET /sessions` (user -> port, started_at, last_seen, alive).
        """
        url = f"{self.base_url}/sessions"
        resp = self._client._perform_request("GET", url)
        return self._client._json_or_raise(resp)

    def restart_session(self) -> dict[str, Any]:
        """Restart the worker tied to the authenticated/current user."""
        url = f"{self.base_url}/sessions/self/restart"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def shutdown_session(self) -> dict[str, Any]:
        """Shut down the worker tied to the authenticated/current user."""
        url = f"{self.base_url}/sessions/self/shutdown"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def restart_session_for(self, user: str) -> dict[str, Any]:
        """Admin helper to restart another user's worker."""
        url = f"{self.base_url}/sessions/{user}/restart"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def shutdown_session_for(self, user: str) -> dict[str, Any]:
        """Admin helper to shut down another user's worker."""
        url = f"{self.base_url}/sessions/{user}/shutdown"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def disconnect_user_instrument(self, user: str, instrument: str) -> dict[str, Any]:
        """Admin helper to disconnect a specific instrument and release its lock for a user."""
        url = f"{self.base_url}/sessions/{user}/devices/{instrument}/disconnect"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def update_server_repo(self) -> dict[str, Any]:
        """Run `git pull --ff-only` in the lab-server repository via `/system/update`."""
        url = f"{self.base_url}/system/update"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def docs_status(self) -> dict[str, Any]:
        """Return whether the lab-client docs sidecar is running."""
        url = f"{self.base_url}/client-docs/status"
        resp = self._client._perform_request("GET", url)
        return self._client._json_or_raise(resp)

    def start_docs(self) -> dict[str, Any]:
        """Start the lab-client docs server."""
        url = f"{self.base_url}/client-docs/start"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def stop_docs(self) -> dict[str, Any]:
        """Stop the lab-client docs server."""
        url = f"{self.base_url}/client-docs/stop"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def restart_docs(self) -> dict[str, Any]:
        """Restart the lab-client docs server."""
        url = f"{self.base_url}/client-docs/restart"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)

    def update_docs_repo(self) -> dict[str, Any]:
        """Pull the lab-client repository used for docs hosting."""
        url = f"{self.base_url}/client-docs/update"
        resp = self._client._perform_request("POST", url)
        return self._client._json_or_raise(resp)
