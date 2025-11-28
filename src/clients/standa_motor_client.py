from __future__ import annotations

from clients.base_client import LabDeviceClient


class StandaMotorClient(LabDeviceClient):
    """Client for the Standa XIMC motor server driver."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        uri: str | None = None,
        enumerate_network: bool | None = None,
        allow_virtual: bool | None = None,
        default_speed: int | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        """
        Create and connect a Standa motor session on the server.

        Args:
            base_url: Server base URL (e.g., ``http://127.0.0.1:5000``).
            device_name: Key from server config (e.g., ``standa_motor``).
            uri: Explicit device URI (e.g., ``xi-com:\\\\.\\COM5``). When None, the
                server will enumerate and pick the first device.
            enumerate_network: Include network devices during enumeration (server default True).
            allow_virtual: Allow virtual controller if no hardware is found (server default False).
            default_speed: Optional initial speed in controller units (steps/s).
            user: Optional user for server-side locking.
            debug: Include detailed server traces if True.
        """
        super().__init__(base_url, device_name, user=user, debug=debug)
        init_params = {
            "uri": uri,
            "enumerate_network": enumerate_network,
            "allow_virtual": allow_virtual,
            "default_speed": default_speed,
        }
        cleaned = {k: v for k, v in init_params.items() if v is not None}
        self.init_params = cleaned
        self._initialize_device(cleaned)

    # Properties --------------------------------------------------
    @property
    def uri(self) -> str | None:
        return self.get_property("uri")

    @property
    def position(self) -> dict:
        """Current position dict with 'steps' and 'microsteps'."""
        return dict(self.get_property("position"))

    @position.setter
    def position(self, value: dict) -> None:
        self.set_property("position", value)

    @property
    def speed(self) -> int:
        return int(self.get_property("speed"))

    @speed.setter
    def speed(self, value: int) -> None:
        self.set_property("speed", int(value))

    # Actions -----------------------------------------------------
    def home(self) -> None:
        self.call("home")

    def move_absolute(self, steps: int, microsteps: int = 0, wait_interval_ms: int = 100) -> None:
        self.call(
            "move_absolute",
            steps=int(steps),
            microsteps=int(microsteps),
            wait_interval_ms=int(wait_interval_ms),
        )

    def move_relative(self, steps: int, microsteps: int = 0, wait_interval_ms: int = 100) -> None:
        self.call(
            "move_relative",
            steps=int(steps),
            microsteps=int(microsteps),
            wait_interval_ms=int(wait_interval_ms),
        )

    def wait_for_stop(self, interval_ms: int = 100) -> None:
        self.call("wait_for_stop", interval_ms=int(interval_ms))

    def stop(self) -> None:
        self.call("stop")

    def close(self) -> None:
        self.disconnect()
