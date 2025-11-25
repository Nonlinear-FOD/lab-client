from clients.base_client import LabDeviceClient


class SuperKCompactClient(LabDeviceClient):
    """Client for NKTP SuperK Compact.

    Server-side driver: `devices.nktp_superk_compact.SuperKCompact`.

    Args:
        base_url: Base HTTP URL of the server (e.g., ``http://127.0.0.1:5000``).
        device_name: Device key from server config (e.g., ``nktp_superk_1``).
        port: COM port number or string (e.g., ``3`` or ``\"COM3\"``).
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        port: int | str,
        user: str | None = None,
        debug: bool = False,
    ):
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device({"port": port})

    def enable(self) -> None:
        """Turn emission on."""
        self.call("enable")

    def disable(self) -> None:
        """Turn emission off."""
        self.call("disable")

    @property
    def emission(self) -> int:
        """Emission state (0/1)."""
        return self.get_property("emission")

    @emission.setter
    def emission(self, value: int | bool) -> None:
        self.set_property("emission", int(value))

    @property
    def reprate(self) -> int:
        """Pulse repetition rate in Hz."""
        return self.get_property("reprate")

    @reprate.setter
    def reprate(self, value: int) -> None:
        self.set_property("reprate", value)

    @property
    def power_percentage(self) -> int:
        """Power as a percentage (0-100)."""
        return self.get_property("power_percentage")

    @power_percentage.setter
    def power_percentage(self, value: int) -> None:
        self.set_property("power_percentage", value)
