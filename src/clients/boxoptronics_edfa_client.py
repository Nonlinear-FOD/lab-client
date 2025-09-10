from .base_client import LabDeviceClient


class BoxoptronicsEDFAClient(LabDeviceClient):
    """Client for Box Optronics EDFA amplifier.

    Server-side driver: devices.boxoptronics_edfa.BoxoptronicsEDFA
    """
    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        init_params = {"com_port": com_port}
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    def close(self) -> None:
        self.disconnect()

    def read_status(self) -> dict:
        return self.call("read_status")

    @property
    def target_power_dbm(self) -> float:
        return self.get_property("target_power_dbm")

    @target_power_dbm.setter
    def target_power_dbm(self, value: float) -> None:
        self.set_property("target_power_dbm", value)

    @property
    def mode(self) -> str:
        return self.get_property("mode")

    @mode.setter
    def mode(self, value: int | str) -> None:
        self.set_property("mode", value)

    @property
    def target_current_mA(self) -> int:
        return self.get_property("target_current_mA")

    @target_current_mA.setter
    def target_current_mA(self, value: int) -> None:
        self.set_property("target_current_mA", value)

    @property
    def current_limit_mA(self) -> int:
        return self.get_property("current_limit_mA")

    def get_temps(self) -> dict:
        return self.call("get_temps")

    @property
    def soft_active(self) -> int:
        return self.get_property("soft_active")

    @soft_active.setter
    def soft_active(self, value: bool) -> None:
        self.set_property("soft_active", value)

    def enable(self) -> None:
        self.call("enable")

    def disable(self) -> None:
        self.call("disable")

    def status(self) -> bool:
        return self.call("status")
