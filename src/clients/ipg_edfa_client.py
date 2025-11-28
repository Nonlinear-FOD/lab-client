from .base_client import LabDeviceClient


class IPGEDFAClient(LabDeviceClient):
    """Client for Box Optronics EDFA.

    Server-side driver: `devices.boxoptronics_edfa.BoxoptronicsEDFA`.

    Args:
        base_url: Base HTTP URL of the server.
        device_name: Device key from server config (e.g., `boxoptronics_edfa`).
        com_port: Serial port index/number for the EDFA controller.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        init_params = {"GPIB_address": GPIB_address, "GPIB_bus": GPIB_bus}
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    def close(self) -> None:
        self.disconnect()

    @property
    def power_unit(self) -> str:
        """Power unit (dBm or W)."""
        return self.get_property("power_unit")

    @power_unit.setter
    def power_unit(self, value: str) -> None:
        self.set_property("power_unit", value)

    def write(self, command: str) -> None:
        """Send a raw SCPI/text command to the OSA."""
        self.call("write", command=command)

    def query(self, command: str) -> str:
        """Send a raw query command and return the string response."""
        return self.call("query", command=command)