from __future__ import annotations

from typing import Any

from clients.base_client import LabDeviceClient


class TopticaDLCLaserClient(LabDeviceClient):
    """HTTP client for the Toptica DLCpro server driver."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        **init_overrides: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        if init_overrides:
            self._initialize_device(init_overrides)

    # ------------------------------------------------------------------ lifecycle helpers
    def enable(self) -> dict[str, Any]:
        return dict(self.call("enable"))

    def disable(self) -> dict[str, Any]:
        return dict(self.call("disable"))

    def get_limits(self) -> dict[str, Any]:
        return dict(self.call("get_limits_from_dlc"))

    # ------------------------------------------------------------------ properties
    @property
    def wavelength(self) -> float | None:
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int | None) -> None:
        self.set_property("wavelength", value)

    @property
    def wavelength_actual(self) -> float | None:
        return self.get_property("wavelength_actual")

    @property
    def current(self) -> float:
        return self.get_property("current")

    @current.setter
    def current(self, value: float | int) -> None:
        self.set_property("current", float(value))

    @property
    def current_enabled(self) -> bool:
        return bool(self.get_property("current_enabled"))

    @current_enabled.setter
    def current_enabled(self, value: bool) -> None:
        self.set_property("current_enabled", bool(value))

    @property
    def emission(self) -> bool:
        return bool(self.get_property("emission"))
