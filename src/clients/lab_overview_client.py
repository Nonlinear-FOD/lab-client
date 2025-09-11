from __future__ import annotations

from typing import Any
import requests


class LabOverviewClient:
    """Read-only client for overview and system endpoints. Can be used to see what devices are
    connected and which are currently used.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        user: Optional user name for lock-aware endpoints (passed as `X-User`).
    """

    def __init__(self, base_url: str, user: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.user = user

    def _headers(self) -> dict[str, str]:
        return {"X-User": self.user} if self.user else {}

    def _json_or_raise(self, resp: requests.Response) -> dict[str, Any]:
        resp.raise_for_status()
        return resp.json()

    def devices(self) -> dict[str, Any]:
        """Return connection/lock status for all configured devices.

        Returns:
            Mapping of device name to `{"connected": bool, "connected_since": str|None, "used_by": str|None}`.
        """
        url = f"{self.base_url}/overview/devices"
        return self._json_or_raise(requests.get(url, headers=self._headers()))

    def list_used_instruments(self) -> dict[str, Any]:
        """Return current locks: which user holds which device (if any)."""
        url = f"{self.base_url}/overview/locks"
        return self._json_or_raise(requests.get(url, headers=self._headers()))

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
        try:
            return self._json_or_raise(
                requests.get(url, params=params, headers=self._headers())
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not retrieve connected instruments from {url}: {e}"
            ) from e
