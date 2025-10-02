from __future__ import annotations

from clients.base_client import LabDeviceClient


class KinesisMotorClient(LabDeviceClient):
    """Client for Thorlabs KCube DC Servo single-axis stages.

    Server driver: ``devices.kinesis_motor.KinesisMotor``.
    Coordinates are expressed in millimetres, matching the cube display when a
    valid stage file is active on the controller.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        serial: int | str | None = None,
        index: int | None = None,
        device_type: str | None = None,
        timeout_s: float | None = None,
        kinesis_path: str | None = None,
        polling_interval_ms: int | None = None,
        stage_name: str | None = None,
        use_device_settings: bool | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        """Connect to a KCube stage exposed by the lab server."""
        super().__init__(base_url, device_name, user=user, debug=debug)
        init_params = {
            "serial": serial,
            "index": index,
            "timeout_s": timeout_s,
            "device_type": device_type,
            "kinesis_path": kinesis_path,
            "polling_interval_ms": polling_interval_ms,
            "stage_name": stage_name,
            "use_device_settings": use_device_settings,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        self._initialize_device(self.init_params)

    # Motion ------------------------------------------------------
    def home(self, timeout_s: float = 60.0) -> None:
        """Home the axis and block until completion."""
        self.call("home", timeout_s=float(timeout_s))

    def move_relative(self, delta: float, timeout_s: float = 60.0) -> None:
        """Move by a relative offset in millimetres."""
        self.call(
            "move_relative",
            delta=float(delta),
            timeout_s=float(timeout_s),
        )

    def stop(self) -> None:
        """Stop motion immediately."""
        self.call("stop")

    @property
    def position(self) -> float:
        """Return the current stage position in millimetres."""
        return float(self.get_property("position"))

    @position.setter
    def position(self, pos: float) -> None:
        """Move to an absolute position in millimetres."""
        self.set_property(
            "position",
            pos,
        )

    @property
    def timeout_s(self) -> float:
        """Return the current stage timeout_s in millimetres."""
        return float(self.get_property("timeout_s"))

    @timeout_s.setter
    def timeout_s(self, ts: float) -> None:
        """Sets the timeout in seconds for multiple commands."""
        self.set_property(
            "timeout_s",
            ts,
        )

    def is_connected(self) -> bool:
        """Return ``True`` when the device is connected on the server."""
        return bool(self.call("is_connected"))

    def close(self) -> None:
        """Release the remote device and clear server locks."""
        self.disconnect()
