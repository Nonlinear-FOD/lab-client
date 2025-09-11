from typing import Any

from .base_client import LabDeviceClient


class ThorlabsPMClient(LabDeviceClient):
    """Client for Thorlabs PM100 power meter.

    Server-side driver: `devices.thorlabs_pm.ThorlabsPM`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `thorlabspm_1`).
        resource: VISA resource string (e.g., `USB0::...::INSTR`).
        timeout_s: I/O timeout in seconds.
        scale: `'lin'` (Watts) or `'log'` (dBm).
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.

    Notes:
        - `.close()` delegates to `.disconnect()` to drop the server instance and release the lock.
        - When `scale='log'`, values are `10*log10(mW)`.
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
        """Active correction wavelength in nm."""
        return float(self.get_property("wavelength"))

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", float(value))

    @property
    def scale(self) -> str:
        """Readout scale: `'lin'` (W) or `'log'` (dBm)."""
        return str(self.get_property("scale"))

    @scale.setter
    def scale(self, value: str) -> None:
        self.set_property("scale", value)

    # Measurements -----------------------------------------------
    def read(self, sleep: bool = True) -> float:
        """Read power once.
        
        Parameters
        - sleep: If true, server waits briefly for a fresh reading.
        
        Returns
        - Power in W (`scale='lin'`) or dBm (`scale='log'`).
        """
        return float(self.call("read", sleep=bool(sleep)))

    def close(self) -> None:
        """Release server-side instance and lock (delegates to `.disconnect()`)."""
        self.disconnect()
