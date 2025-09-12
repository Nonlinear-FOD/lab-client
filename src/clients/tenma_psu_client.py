from __future__ import annotations

from typing import Any

from clients.base_client import LabDeviceClient


class TenmaPSUClient(LabDeviceClient):
    """Client for Tenma 72-26xx dual-channel DC power supplies.

    Server driver: ``devices.tenma_dc_p_supply.TenmaPSU``.

    Provides per-channel properties via an active ``channel`` selector (1 or 2),
    plus global controls for output, lock, beep and status.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None,
        channel: int | None = None,
        user: str | None = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        payload: dict[str, Any] = {"com_port": com_port}
        if channel is not None:
            payload["channel"] = int(channel)
        payload.update(kwargs)
        self._initialize_device(payload)

    # ---------- Channel selector ----------
    @property
    def channel(self) -> int:
        """Active output channel (1 or 2)."""
        return int(self.get_property("channel"))

    @channel.setter
    def channel(self, value: int) -> None:
        """Select active output channel (1 or 2)."""
        self.set_property("channel", int(value))

    # ---------- Per-channel properties ----------
    @property
    def voltage_set(self) -> float:
        """Voltage setpoint (V) of the active channel."""
        return float(self.get_property("voltage_set"))

    @voltage_set.setter
    def voltage_set(self, volts: float) -> None:
        """Set voltage setpoint (V) of the active channel."""
        self.set_property("voltage_set", float(volts))

    @property
    def voltage(self) -> float:
        """Actual output voltage (V) of the active channel (read-only)."""
        return float(self.get_property("voltage"))

    @property
    def current_set(self) -> float:
        """Current limit setpoint (A) of the active channel."""
        return float(self.get_property("current_set"))

    @current_set.setter
    def current_set(self, amps: float) -> None:
        """Set current limit setpoint (A) of the active channel."""
        self.set_property("current_set", float(amps))

    @property
    def current(self) -> float:
        """Actual output current (A) of the active channel (read-only)."""
        return float(self.get_property("current"))

    # ---------- Output and panel ----------
    @property
    def output(self) -> bool:
        """Global output state (True=ON, False=OFF)."""
        return bool(self.get_property("output"))

    @output.setter
    def output(self, enabled: bool) -> None:
        """Turn global output ON/OFF."""
        self.set_property("output", bool(enabled))

    def lock(self, enabled: bool) -> None:
        """Lock or unlock the power supply front panel."""
        self.call("lock", enabled=bool(enabled))

    def beep(self, enabled: bool) -> None:
        """Enable or disable the front-panel sounder (beep)."""
        self.call("beep", enabled=bool(enabled))

    def status(self) -> dict:
        """Return decoded status including CV/CC modes and output state."""
        return dict(self.call("status"))

    def recall(self, slot: int) -> None:
        """Recall a stored panel setting (slots 1..5)."""
        self.call("recall", slot=int(slot))

    def close(self) -> None:
        self.disconnect()
