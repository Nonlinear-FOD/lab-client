from __future__ import annotations

from typing import Any

from .base_client import LabDeviceClient


class SLMClient(LabDeviceClient):
    """
    Client for the SLMDisplay server device (headless rendering to the SLM monitor).
    Mirrors the legacy MATLAB GUI knobs as properties.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str = "slm_1",
        user: str | None = None,
        debug: bool = False,
    ):
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device({})

    # -------- Bulk settings --------
    @property
    def settings(self) -> dict[str, Any]:
        return self.get_property("settings")

    @settings.setter
    def settings(self, value: dict[str, Any]) -> None:
        self.set_property("settings", value)

    # -------- Actions --------
    def render(
        self, *, settings: dict[str, Any] | None = None, return_preview: bool = False
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"return_preview": bool(return_preview)}
        if settings is not None:
            payload["settings"] = settings
        return self.call("render", **payload)

    def clear(self) -> dict[str, Any]:
        return self.call("clear")

    def close(self) -> None:
        try:
            self.call("close")
        finally:
            self.disconnect()
