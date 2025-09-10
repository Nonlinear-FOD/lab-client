from typing import Any

from .base_client import LabDeviceClient


class ThorlabsPMClient(LabDeviceClient):
    """Client for Thorlabs PM100 power meter.
    Server-side driver: devices.thorlabs_pm.ThorlabsPM
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        resource: str | None = None,
        timeout_s: float | None = None,
        scale: str | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        init_params: dict[str, Any] = {
            "resource": resource,
            "timeout_s": timeout_s,
            "scale": scale,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    # Properties --------------------------------------------------
    @property
    def wavelength(self) -> float:
        return float(self.get_property("wavelength"))

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", float(value))

    @property
    def scale(self) -> str:
        return str(self.get_property("scale"))

    @scale.setter
    def scale(self, value: str) -> None:
        self.set_property("scale", value)

    # Measurements -----------------------------------------------
    def read(self, sleep: bool = True) -> float:
        return float(self.call("read", sleep=bool(sleep)))

    def close(self) -> None:
        # Delegate teardown to server-side disconnect
        self.disconnect()
