from __future__ import annotations

from typing import Any
import requests


class LabOverviewClient:
    """
    Read-only client for overview endpoints.
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
        url = f"{self.base_url}/overview/devices"
        return self._json_or_raise(requests.get(url, headers=self._headers()))

    def list_used_instruments(self) -> dict[str, Any]:
        url = f"{self.base_url}/overview/locks"
        return self._json_or_raise(requests.get(url, headers=self._headers()))

    def list_connected_instruments(
        self, probe_idn: bool = False, timeout_ms: int = 300
    ) -> dict[str, Any]:
        """
        Returns VISA resources discovered on the server.
        If probe_idn=True, the server will try '*IDN?' on each resource
        using the provided timeout.
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
