from __future__ import annotations

from clients.base_client import LabDeviceClient


class Zaber1DMotorClient(LabDeviceClient):
    """Client for a single-axis Zaber motor.

    Server driver: ``devices.zaber_1d_motor.Zaber1DMotor``.

    Overview:
      - Select units with ``units`` property (e.g., ``'mm'``, ``'um'``, ``'in'``).
      - ``home()`` homes the axis if needed; ``move_relative(dx)`` moves by ``dx`` in the active units.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        device_index: int | None = None,
        axis_index: int | None = None,
        units: str | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        """Create and connect a Zaber 1D motor session on the server.

        Args:
            base_url: Server base URL (e.g., ``http://127.0.0.1:5000``).
            device_name: Key from server config (e.g., ``zaber_1d``).
            com_port: Windows COM number (e.g., 3 → COM3). Leave ``None`` to use server default.
            device_index: 1-based device index from detection (default 1).
            axis_index: 1-based axis index on the selected device (default 1).
            units: Initial units key (e.g., ``'mm'``, ``'um'``, ``'in'``). Server default applies when ``None``.
            user: Optional user used for server-side locking.
            debug: Include detailed error traces from server if ``True``.
        """
        super().__init__(base_url, device_name, user=user, debug=debug)
        init_params = {
            "com_port": com_port,
            "device_index": device_index,
            "axis_index": axis_index,
            "units": units,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        self._initialize_device(self.init_params)

    # Properties --------------------------------------------------
    @property
    def units(self) -> str:
        """Current length units key used by the server (e.g., ``'um'``)."""
        return str(self.get_property("units"))

    @units.setter
    def units(self, value: str) -> None:
        """Set the length units key (validated on the server)."""
        self.set_property("units", str(value))

    # Actions -----------------------------------------------------
    def home(self) -> None:
        """Home the axis if not already homed (server-side)."""
        self.call("home")

    def move_relative(self, distance: float) -> None:
        """Move by a relative distance in the active units (server-side)."""
        self.call("move_relative", distance=float(distance))

    def close(self) -> None:
        """Disconnect and release the server-side instance and lock."""
        self.disconnect()
