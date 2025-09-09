from clients.base_client import LabDeviceClient
from typing import Any


class ThorlabsMPC320Client(LabDeviceClient):
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
        return int(self.get_property("velocity"))

    @velocity.setter
    def velocity(self, value: int) -> None:
        self.set_property("velocity", int(value))

    # Motion methods
    def get_position(self, paddle_num: int) -> float:
        return float(self.call("get_position", paddle_num=paddle_num))

    def set_position(self, paddle_num: int, position: float, timeout_s: float | None = None) -> None:
        payload: dict[str, Any] = {"paddle_num": paddle_num, "position": float(position)}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("set_position", **payload)

    def move_relative(self, paddle_num: int, delta: float, timeout_s: float | None = None) -> None:
        payload: dict[str, Any] = {"paddle_num": paddle_num, "delta": float(delta)}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("move_relative", **payload)

    def home(self, paddle_num: int, timeout_s: float | None = None) -> None:
        payload: dict[str, Any] = {"paddle_num": paddle_num}
        if timeout_s is not None:
            payload["timeout_s"] = float(timeout_s)
        self.call("home", **payload)

    def close(self) -> None:
        self.call("close")
