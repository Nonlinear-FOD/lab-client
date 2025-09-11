from typing import Any, Protocol

from .base_client import LabDeviceClient


class TunableLaserClientBase(LabDeviceClient):
    """Common helpers for tunable lasers (wavelength, enable/disable).

    Mixed into device-specific clients; not bound to a single server driver.

    Notes:
        - All laser clients expose `wavelength` and typically a `power` property
          (via `PowerSettable`).
        - `enable()` and `disable()` control output state where supported.
        - `.close()` disables output then disconnects the server-side instance.
    """

    # Common helpers most tunable lasers expose
    @property
    def wavelength(self) -> float:
        """Current output wavelength in nm (property)."""
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        """Set target wavelength in nm (property setter)."""
        self.set_property("wavelength", value)

    def enable(self) -> None:
        """Enable laser output (device must support it)."""
        self.call("enable")

    def disable(self) -> None:
        """Disable laser output."""
        self.call("disable")

    def close(self) -> None:
        """Disable output and disconnect the server-side instance."""
        self.disable()
        self.disconnect()

    def write(self, command: str) -> None:
        """Send a raw command to the underlying device (driver-specific)."""
        self.call("write", command=command)

    def query(self, command: str) -> str:
        """Send a raw query and return the response string (driver-specific)."""
        return self.call("query", command=command)


class _HasProps(Protocol):
    """To avoid circular import of LabDeviceClient by not importing it in both TunableLaserClientBase and PowerSettable"""

    def get_property(self, name: str) -> Any: ...
    def set_property(self, name: str, value: Any) -> None: ...
    def call(self, name: str, **kwargs: Any) -> None: ...


class PowerSettable(_HasProps):
    """Mixin exposing a standard `power` property on laser clients. If the laser has this property, its power can be set."""

    @property
    def power(self) -> float:
        """Current output power (units depend on device)."""
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        """Set output power to `value` (device-specific units)."""
        self.set_property("power", value)


class OSAClientLike(Protocol):
    @property
    def device_name(self) -> str: ...


class OSATuningClientMixin(_HasProps):
    """Mixin providing OSA-assisted wavelength adjustment on lasers."""

    def adjust_wavelength(
        self,
        osa: OSAClientLike | str,
        res: float = 0.01,
        sens: str = "SMID",
        samples: int = 10001,
        tol_nm: float = 0.005,
    ) -> None:
        """Adjust wavelength by maximizing OSA peak near current center.

        Args:
            osa: OSA client or device name registered on the server.
            res: OSA resolution bandwidth in nm (e.g., 0.01).
            sens: OSA sensitivity (e.g., `SMID`).
            samples: Number of OSA samples to acquire per sweep.
            tol_nm: Stop when absolute wavelength error < `tol_nm`.
        """
        # self.call(...) comes from LabDeviceClient via your client base
        name = osa if isinstance(osa, str) else osa.device_name
        self.call(
            "adjust_wavelength",
            osa_device=name,  # <-- pass the name only
            res=res,
            sens=sens,
            samples=samples,
            tol_nm=tol_nm,
        )
