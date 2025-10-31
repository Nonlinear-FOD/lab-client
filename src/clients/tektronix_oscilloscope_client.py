from __future__ import annotations

from typing import Any, Tuple

import numpy as np

from clients.base_client import LabDeviceClient


class TektronixOscilloscopeClient(LabDeviceClient):
    """Client for the generic SCPI oscilloscope driver.

    Mirrors the Tektronix-style DATA/WFMOutpre/CURVE sequence and exposes a
    small set of convenience properties (timebase, scale, offset). Use
    ``read_waveform`` to fetch the displayed trace as numpy arrays.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        *,
        connection_resource: str | None = None,
        host: str | None = None,
        port: int | None = None,
        gpib_address: int | None = None,
        gpib_bus: int | None = None,
        channel: int | None = None,
        timeout_s: float | None = None,
        user: str | None = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        payload: dict[str, Any] = {
            "connection_resource": connection_resource,
            "host": host,
            "port": port,
            "gpib_address": gpib_address,
            "gpib_bus": gpib_bus,
            "channel": channel,
            "timeout_s": timeout_s,
        }
        payload.update(kwargs)
        self._initialize_device(payload)

    # ---------------- Channel ----------------
    @property
    def channel(self) -> int:
        return int(self.get_property("channel"))

    @channel.setter
    def channel(self, value: int) -> None:
        self.set_property("channel", int(value))

    # ---------------- Timebase ----------------
    @property
    def time_scale(self) -> float:
        return float(self.get_property("time_scale"))

    @time_scale.setter
    def time_scale(self, seconds_per_div: float) -> None:
        self.set_property("time_scale", float(seconds_per_div))

    @property
    def position(self) -> float:
        return float(self.get_property("position"))

    @position.setter
    def position(self, offset: float) -> None:
        self.set_property("position", float(offset))

    @property
    def sample_rate(self) -> float:
        return float(self.get_property("sample_rate"))

    @sample_rate.setter
    def sample_rate(self, rate: float) -> None:
        self.set_property("sample_rate", float(rate))

    @property
    def resolution(self) -> float:
        return float(self.get_property("resolution"))

    @resolution.setter
    def resolution(self, value: float) -> None:
        self.set_property("resolution", float(value))

    # ---------------- Vertical ----------------
    @property
    def vertical_scale(self) -> float:
        return float(self.get_property("vertical_scale"))

    @vertical_scale.setter
    def vertical_scale(self, volts_per_div: float) -> None:
        self.set_property("vertical_scale", float(volts_per_div))

    @property
    def offset(self) -> float:
        return float(self.get_property("offset"))

    @offset.setter
    def offset(self, volts: float) -> None:
        self.set_property("offset", float(volts))

    # ---------------- Acquisition ----------------
    def read_waveform(
        self,
        *,
        encoding: str = "ASCII",
        start: int | None = None,
        stop: int | None = None,
    ) -> Tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        """Fetch the current waveform.

        Returns:
            tuple: ``(times, voltages, metadata)`` where the arrays are numpy
            vectors and metadata is a dictionary containing the scaling values
            reported by the scope.
        """
        payload: dict[str, Any] = {"encoding": encoding}
        if start is not None:
            payload["start"] = int(start)
        if stop is not None:
            payload["stop"] = int(stop)

        result = self.call("read_waveform", **payload)
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected response from read_waveform endpoint")

        times = np.asarray(result.get("times", []), dtype=float)
        voltages = np.asarray(result.get("voltages", []), dtype=float)
        metadata = dict(result.get("metadata", {}))
        return times, voltages, metadata

    def close(self) -> None:
        self.disconnect()
