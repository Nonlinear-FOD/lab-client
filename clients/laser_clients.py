import sys
import serial
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from clients.base_client import LabDeviceClient
from clients.osa_clients import OSAClient


class AndoLaserClient(LabDeviceClient):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        target_wavelength: float | int,
        power: float | int,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        wl_interp: bool = False,
    ):
        self.init_params = {
            "wavelength": target_wavelength,
            "power": power,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
        }
        super().__init__(base_url, device_name)
        self._initialize_device(self.init_params)

    @property
    def wavelength(self):
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    @property
    def power(self):
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        self.set_property("power", value)

    @property
    def linewidth(self):
        return self.get_property("linewidth")

    @linewidth.setter
    def linewidth(self, value: int) -> None:
        self.set_property("linewidth", value)

    def enable(self) -> None:
        self.call_method("enable")

    def disable(self) -> None:
        self.call_method("disable")

    def close(self) -> None:
        self.call_method("close")

    def write(self, command: str) -> None:
        self.call_method("write", command)

    def query(self, command: str) -> None:
        self.call_method("query", command)


class AgilentLaserClient(LabDeviceClient):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        target_wavelength: float | int,
        power: float | int,
        source: int,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        wl_interp: bool = False,
    ):
        self.init_params = {
            "wavelength": target_wavelength,
            "power": power,
            "source": source,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
        }
        super().__init__(base_url, device_name)
        self._initialize_device(self.init_params)

    @property
    def source(self):
        return self.get_property("source")

    @source.setter
    def source(self, value: int) -> None:
        self.set_property("source", value)

    @property
    def wavelength(self) -> float:
        wl = self.get_property("wavelength")
        assert isinstance(wl, float) or isinstance(wl, int)
        return wl

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    @property
    def unit(self):
        return self.get_property("unit")

    @unit.setter
    def unit(self, value: float | int) -> None:
        self.set_property("unit", value)

    @property
    def power(self):
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        self.set_property("power", value)

    def enable(self) -> None:
        self.call_method("enable")

    def disable(self) -> None:
        self.call_method("disable")

    def write(self, command: str) -> None:
        self.call_method("write", command)

    def query(self, command: str) -> str:
        return self.call_method("query", command, expect_response=True)

    def close(self) -> None:
        self.call_method("close")


class TiSapphireClient(LabDeviceClient):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        NSL: int = 10,
        PSL: int = 10,
    ):
        self.init_params = {
            "com_port": com_port,
            "NSL": NSL,
            "PSL": PSL,
        }
        super().__init__(base_url, device_name)
        self._initialize_device(self.init_params)

    @property
    def wavelength(self):
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    def delta_wl_nm(self, value: float) -> None:
        self.call_method("delta_wl_nm", value)

    def delta_wl_arb(self, value: float) -> None:
        self.call_method("delta_wl_arb", value)

    def get_pos(self) -> None:
        self.call_method("get_pos")

    def adjust_wavelength(
        self,
        osa: OSAClient,
        res: float = 0.01,
        sens: str = "SMID",
        num_samples: int = 10001,
        target_error: float = 0.1,
    ):
        self.call_method("adjust_wavelength", osa, res, sens, num_samples, target_error)

    def calibrate(
        self,
        osa: OSAClient,
        cal_start: float | int,
        cal_end: float | int,
        cal_step: float | int,
        interval: float | int = 10,
        padding: float | int = 2,
        res: float | int = 1,
    ):
        self.call_method(
            "calibrate", osa, cal_start, cal_end, cal_step, interval, padding, res
        )

    def set_wavelength_iterative_method(
        self,
        target_wl: float | int,
        osa: OSAClient,
        min_peak_val: float | int = -45,
        osa_rough_res: float | int = 0.5,
        osa_fine_res: float | int = 0.01,
        error_tolerance: float | int = 0.05,
    ):
        self.call_method(
            "set_wavelength_iterative_method",
            target_wl,
            osa,
            min_peak_val,
            osa_rough_res,
            osa_fine_res,
            error_tolerance,
        )


class VerdiLaserClient(LabDeviceClient):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity=serial.PARITY_NONE,
        stopbits: int = 1,
        timeout: int = 2,
    ):
        self.init_params = {
            "com_port": com_port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
        }
        super().__init__(base_url, device_name)
        self._initialize_device(self.init_params)

    def port_pause(self) -> None:
        self.call_method("port_pause")

    def port_clear(self) -> None:
        self.call_method("port_clear")

    def port_close(self) -> None:
        self.call_method("port_close")

    def laser_home(self) -> None:
        self.call_method("laser_home")

    def in_waiting(self) -> None:
        self.call_method("in_waiting")

    def laser_query(self) -> None:
        self.call_method("laser_query")

    def shutdown(self) -> None:
        self.call_method("shutdown")

    def standby_on(self) -> None:
        self.call_method("standby_on")

    def active_on(self) -> None:
        self.call_method("active_on")

    @property
    def shutter(self):
        return self.get_property("shutter")

    @shutter.setter
    def shutter(self, value: int) -> None:
        self.set_property("shutter", value)

    @property
    def power(self):
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        self.set_property("power", value)


if __name__ == "__main__":
    ip = "http://100.80.226.33:5000"
    agilent1 = AgilentLaserClient(ip, "agilent_laser", 1551, power=0, source=1)
    agilent2 = AgilentLaserClient(ip, "agilent_laser", 1551, power=0, source=2)
