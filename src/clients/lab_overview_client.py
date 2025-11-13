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

    def list_connected_instruments(
        self, probe_idn: bool = False, timeout_ms: int = 300
    ) -> dict[str, Any]:
        """Enumerate VISA resources on the server host.

        Args:
            probe_idn: If true, the server queries `*IDN?` for each resource.
            timeout_ms: Timeout in milliseconds for the probe.

        Returns:
            Dict with a `"visa"` key containing resource info and optional IDNs.
        """
        url = f"{self.base_url}/system/resources"
        params = {"probe_idn": str(probe_idn).lower(), "timeout_ms": timeout_ms}
        resp = self._perform_request("GET", url, params=params)
        return self._json_or_raise(resp)

    def _perform_request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
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
                raise ConnectionError(f"Could not reach {self.base_url}: {exc}") from exc

            if (
                resp.status_code == 401
                and self._auth
                and attempts == 0
            ):
                self._auth.reset_session()
                attempts += 1
                continue
            return resp
