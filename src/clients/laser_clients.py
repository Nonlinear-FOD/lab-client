import os
import sys

import serial

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from clients.base_client import LabDeviceClient
from clients.laser_base_clients import (
    OSATuningClientMixin,
    PowerSettable,
    TunableLaserClientBase,
)
from clients.osa_clients import OSAClient


class AndoLaserClient(TunableLaserClientBase, PowerSettable, OSATuningClientMixin):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        target_wavelength: float | int,
        power: float | int,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        wl_interp: bool = False,
        user: str | None = None,
    ):
        self.init_params = {
            "target_wavelength": target_wavelength,
            "power": power,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
        }
        super().__init__(base_url, device_name, user=user)
        self._initialize_device(self.init_params)

    @property
    def linewidth(self):
        return self.get_property("linewidth")

    @linewidth.setter
    def linewidth(self, value: int) -> None:
        self.set_property("linewidth", value)


class AgilentLaserClient(TunableLaserClientBase, PowerSettable, OSATuningClientMixin):
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
        user: str | None = None,
    ):
        self.init_params = {
            "target_wavelength": target_wavelength,
            "power": power,
            "source": source,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
        }
        super().__init__(base_url, device_name, user=user)
        self._initialize_device(self.init_params)

    @property
    def source(self):
        return self.get_property("source")

    @source.setter
    def source(self, value: int) -> None:
        self.set_property("source", value)

    @property
    def unit(self):
        return self.get_property("unit")

    @unit.setter
    def unit(self, value: str) -> None:
        self.set_property("unit", value)


class TiSapphireClient(LabDeviceClient, OSATuningClientMixin):
    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        NSL: int = 10,
        PSL: int = 10,
        smc_path: str | None = None,
        calibration_path: str | None = None,
        initial_wavelength: float | None = None,
        nm_to_pos_slope: float | None = None,
        user: str | None = None,
    ):
        self.init_params = {
            "com_port": com_port,
            "NSL": NSL,
            "PSL": PSL,
            "smc_path": smc_path,
            "calibration_path": calibration_path,
            "initial_wavelength": initial_wavelength,
            "nm_to_pos_slope": nm_to_pos_slope,
        }
        super().__init__(base_url, device_name, user=user)
        self._initialize_device(self.init_params)

    @property
    def wavelength(self) -> float:
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    def delta_wl_nm(self, value: float) -> None:
        self.call("delta_wl_nm", delta_nm=value)

    def delta_wl_arb(self, value: float) -> None:
        self.call("delta_wl_arb", delta_pos=value)

    def get_pos(self) -> float:
        return self.call("get_pos")

    def calibrate(
        self,
        osa: OSAClient,
        cal_start: float | int,
        cal_end: float | int,
        cal_step: float | int,
        interval: float | int = 10,
        padding: float | int = 2,
        res: float | int = 1,
    ) -> None:
        self.call(
            "calibrate",
            osa_device=osa.device_name,  # pass reference, not object
            cal_start=cal_start,
            cal_end=cal_end,
            cal_step=cal_step,
            interval=interval,
            padding=padding,
            res=res,
        )

    def set_wavelength_iterative_method(
        self,
        target_wl: float | int,
        osa: OSAClient,
        min_peak_val: float | int = -45,
        osa_rough_res: float | int = 0.5,
        osa_fine_res: float | int = 0.01,
        error_tolerance: float | int = 0.05,
    ) -> None:
        self.call(
            "set_wavelength_iterative_method",
            target_wl=target_wl,
            osa_device=osa.device_name,
            min_peak_val=min_peak_val,
            osa_rough_res=osa_rough_res,
            osa_fine_res=osa_fine_res,
            error_tolerance=error_tolerance,
        )

    def close(self) -> None:
        self.call("close")


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
        user: str | None = None,
    ):
        self.init_params = {
            "com_port": com_port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
        }
        super().__init__(base_url, device_name, user=user)
        self._initialize_device(self.init_params)

    def port_pause(self) -> None:
        self.call("port_pause")

    def port_clear(self) -> None:
        self.call("port_clear")

    def port_close(self) -> None:
        self.call("port_close")

    def laser_home(self) -> None:
        self.call("laser_home")

    def in_waiting(self) -> None:
        self.call("in_waiting")

    def laser_query(self) -> None:
        self.call("laser_query")

    def shutdown(self) -> None:
        self.call("shutdown")

    def standby_on(self) -> None:
        self.call("standby_on")

    def active_on(self) -> None:
        self.call("active_on")

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
