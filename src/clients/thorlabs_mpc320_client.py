from clients.base_client import LabDeviceClient
from typing import Any


class ThorlabsMPC320Client(LabDeviceClient):
    """Client for Thorlabs MPC320 polarization controller.

    Server-side driver: `devices.thorlabs_mpc320.ThorlabsMPC320`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `mpc320_1`).
        serial/index/kinesis_path/limits/polling_rate_s/initial_velocity: Initialization overrides.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.

    Notes:
        - Motion calls on the server are blocking and accept optional `timeout_s`.
        - `.close()` delegates to `.disconnect()` to drop the server instance and release the lock.
    """
    def __init__(
        self,
        base_url: str,
        device_name: str,
        *,
        serial: str | None = None,
        index: int | None = None,
        kinesis_path: str | None = None,
        limits: tuple[float, float] | None = None,
        polling_rate_s: float | None = None,
        initial_velocity: float | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        init_params: dict[str, Any] = {
            "serial": serial,
            "index": index,
            "kinesis_path": kinesis_path,
            "limits": list(limits) if isinstance(limits, tuple) else limits,
            "polling_rate_s": polling_rate_s,
            "initial_velocity": initial_velocity,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    # Properties
    @property
    def velocity(self) -> int:
        """Current motion velocity (percent)."""
        return int(self.get_property("velocity"))

    @velocity.setter
    def velocity(self, value: int) -> None:
        """Set motion velocity in percent (integer)."""
        self.set_property("velocity", int(value))

    # Motion methods
    def get_position(self, paddle_num: int) -> float:
        """Return current position for `paddle_num` (1–3)."""
        return float(self.call("get_position", paddle_num=paddle_num))

    def set_position(self, paddle_num: int, position: float, timeout_s: float | None = None) -> None:
        """Move `paddle_num` to `position` (deg), blocking until completion or `timeout_s`."""
        payload: dict[str, Any] = {"paddle_num": paddle_num, "position": float(position)}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("set_position", **payload)

    def move_relative(self, paddle_num: int, delta: float, timeout_s: float | None = None) -> None:
        """Relative move for `paddle_num` by `delta` degrees; raises if below device step size."""
        payload: dict[str, Any] = {"paddle_num": paddle_num, "delta": float(delta)}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("move_relative", **payload)

    def home(self, paddle_num: int, timeout_s: float | None = None) -> None:
        """Home the given paddle; blocks until done or `timeout_s`."""
        payload: dict[str, Any] = {"paddle_num": paddle_num}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("home", **payload)

    def close(self) -> None:
        """Release server-side instance and lock (delegates to `.disconnect()`)."""
        self.disconnect()
