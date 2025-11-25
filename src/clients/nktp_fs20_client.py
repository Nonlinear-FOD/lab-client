from clients.base_client import LabDeviceClient


class AeropulseFS20Client(LabDeviceClient):
    """Client for NKTP Aeropulse FS20.

    Server driver: `devices.nktp_fs20.AeropulseFS20`.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        port: int | str,
        auto_open: bool = True,
        user: str | None = None,
        debug: bool = False,
    ):
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device({"port": port, "auto_open": auto_open})

    def enable(self) -> None:
        """Set emission to ON."""
        self.call("enable")

    def disable(self) -> None:
        """Set emission to OFF."""
        self.call("disable")

    def open(self) -> None:
        """Open the device port on the server."""
        self.call("open")

    def close(self) -> None:
        """Close the device port on the server."""
        self.call("close")

    @property
    def emission(self) -> int:
        """Raw emission state (0..4)."""
        return self.get_property("emission")

    @emission.setter
    def emission(self, value: int | bool) -> None:
        self.set_property("emission", int(value) if isinstance(value, bool) else value)

    @property
    def aom2_power_percentage(self) -> float:
        """AOM2 power in % (0–100)."""
        return float(self.get_property("aom2_power_percentage"))

    @aom2_power_percentage.setter
    def aom2_power_percentage(self, value: float) -> None:
        self.set_property("aom2_power_percentage", value)

    @property
    def booster_power_percentage(self) -> float:
        """Booster power in % (0–100)."""
        return float(self.get_property("booster_power_percentage"))

    @booster_power_percentage.setter
    def booster_power_percentage(self, value: float) -> None:
        self.set_property("booster_power_percentage", value)

    @property
    def reprate_hz(self) -> float:
        """Repetition rate in Hz."""
        return float(self.get_property("reprate_hz"))

    @reprate_hz.setter
    def reprate_hz(self, value: float) -> None:
        self.set_property("reprate_hz", value)

    @property
    def peak_power(self) -> float:
        """Peak power readback (%)."""
        return float(self.get_property("peak_power"))

    @property
    def beta2_param(self) -> float:
        return float(self.get_property("beta2_param"))

    @beta2_param.setter
    def beta2_param(self, value: float) -> None:
        self.set_property("beta2_param", value)

    @property
    def beta3_param(self) -> float:
        return float(self.get_property("beta3_param"))

    @beta3_param.setter
    def beta3_param(self, value: float) -> None:
        self.set_property("beta3_param", value)

    @property
    def beta4_param(self) -> float:
        return float(self.get_property("beta4_param"))

    @beta4_param.setter
    def beta4_param(self, value: float) -> None:
        self.set_property("beta4_param", value)

    @property
    def wl_offset(self) -> float:
        return float(self.get_property("wl_offset"))

    @wl_offset.setter
    def wl_offset(self, value: float) -> None:
        self.set_property("wl_offset", value)
