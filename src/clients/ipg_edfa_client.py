from .base_client import LabDeviceClient
import time
import numpy as np


class IPGEDFAClient(LabDeviceClient):
    """Client for IPG EDFA laser amplifier.

    Server-side driver: `devices.ipg_edfa.IPGEDFA`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `ipg_edfa_1`).
        GPIB_address: Optional override for GPIB address.
        GPIB_bus: Optional override for GPIB bus.
        auto_connect: Automatically open the transport on init.
        user: Optional user name for server-side locking.
        debug: When True, server returns detailed error payloads.

    Notes:
        - Properties mirror the server-side IPGEDFA class.
        - Use `.close()` to release the server instance and any locks.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        GPIB_address: int | str | None = None,
        GPIB_bus: int | None = None,
        auto_connect: bool | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        init_params = {
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "auto_connect": auto_connect,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    # --- Power Unit ---
    @property
    def power_unit(self) -> str:
        """Current power unit (`dBm` or `W`)."""
        return self.get_property("power_unit")

    @power_unit.setter
    def power_unit(self, unit: str) -> None:
        self.set_property("power_unit", unit)

    # --- Emission ---
    @property
    def emission(self) -> int:
        """Emission state (0 = off, 1 = on)."""
        return self.get_property("emission")

    @emission.setter
    def emission(self, value: int) -> None:
        self.set_property("emission", value)

    # --- Mode ---
    @property
    def mode(self) -> str:
        """Current control mode (`APC`, `ACC`, `AGC`)."""
        return self.get_property("mode")

    @mode.setter
    def mode(self, value: str) -> None:
        self.set_property("mode", value)

    # --- Power / Gain / Current Set Points ---
    @property
    def power_set_point(self) -> str:
        return self.get_property("power_set_point")

    @power_set_point.setter
    def power_set_point(self, value: str) -> None:
        self.set_property("power_set_point", value)

    @property
    def gain_set_point(self) -> str:
        return self.get_property("gain_set_point")

    @gain_set_point.setter
    def gain_set_point(self, value: str) -> None:
        self.set_property("gain_set_point", value)

    @property
    def current_set_point(self) -> str:
        return self.get_property("current_set_point")

    @current_set_point.setter
    def current_set_point(self, value: str) -> None:
        self.set_property("current_set_point", value)

    # --- Readback Methods ---
    def input_power(self) -> float:
        """Read the current input power in the configured units."""
        return float(self.call("input_power"))

    def back_reflection_level(self) -> str:
        """Read the back-reflection power level."""
        return self.call("back_reflection_level")

    def read_diode_current(self) -> float:
        """Read the laser diode current."""
        return float(self.call("read_diode_current"))

    def read_output_power(self) -> str:
        """Read the output power of the EDFA."""
        return self.call("read_output_power")

    def stat(self) -> str:
        """Read raw 32-bit status string from device."""
        return self.call("stat")

    # --- Low-level SCPI / command access ---
    def write(self, command: str) -> None:
        """Send a raw command to the EDFA."""
        self.call("write", cmd=command)

    def query(self, command: str) -> str:
        """Send a raw query command and return the response."""
        return self.call("query", cmd=command)

    # --- Close ---
    def close(self) -> None:
        """Release server-side instance and lock."""
        self.disconnect()



 
