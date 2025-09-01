from typing import Any, Protocol

import numpy as np

from .base_client import LabDeviceClient
from .osa_clients import OSAClient


class TunableLaserClientBase(LabDeviceClient):
    # Common helpers most tunable lasers expose
    @property
    def wavelength(self) -> float:
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    def enable(self) -> None:
        self.call("enable")

    def disable(self) -> None:
        self.call("disable")

    def close(self) -> None:
        self.disable()
        self.call("close")

    def write(self, command: str) -> None:
        self.call("write", command=command)

    def query(self, command: str) -> str:
        return self.call("query", command=command)


class _HasProps(Protocol):
    """To avoid circular import of LabDeviceClient by not importing it in both TunableLaserClientBase and PowerSettable"""

    def get_property(self, name: str) -> Any: ...
    def set_property(self, name: str, value: Any) -> None: ...
    def call(self, name: str, **kwargs: Any) -> None: ...


class PowerSettable(_HasProps):
    @property
    def power(self) -> float:
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        self.set_property("power", value)


class OSAClientLike(Protocol):
    @property
    def device_name(self) -> str: ...


class OSATuningClientMixin(_HasProps):
    def adjust_wavelength(
        self,
        osa: OSAClientLike | str,
        res: float = 0.01,
        sens: str = "SMID",
        samples: int = 10001,
        tol_nm: float = 0.005,
    ) -> None:
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
