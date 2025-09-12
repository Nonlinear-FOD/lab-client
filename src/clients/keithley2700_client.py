from __future__ import annotations

from clients.base_client import LabDeviceClient


class Keithley2700Client(LabDeviceClient):
    """Minimal client for Keithley 2700 multimeter (voltage fetch only).

    Server driver: ``devices.keithley_2700.Keithley2700``.

    Assumes the instrument is configured manually on the front panel. The
    only method exposed fetches the latest reading using ``FETCh?`` on the
    server and returns it as a float.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        GPIB_bus: int | None = None,
        GPIB_address: int | None = None,
        timeout_s: float | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        payload = {
            "GPIB_bus": GPIB_bus,
            "GPIB_address": GPIB_address,
            "timeout_s": timeout_s,
        }
        # Drop None to let server defaults apply
        self._initialize_device({k: v for k, v in payload.items() if v is not None})

    def read_voltage(self) -> float:
        """Fetch the latest reading as a float via the server."""
        return float(self.call("read_voltage"))

    def close(self) -> None:
        self.disconnect()
