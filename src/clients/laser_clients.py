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
    """Client for Ando tunable laser.

    Server-side driver: `devices.laser_control.AndoLaser`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `ando_laser_1`).
        target_wavelength: Initial wavelength (nm).
        power: Initial output power (device units; see driver docs).
        GPIB_address: Optional override for GPIB address.
        GPIB_bus: Optional override for GPIB bus.
        wl_interp: If true, use interpolation for wavelength moves where supported.
        timeout_s: Transport timeout in seconds.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        target_wavelength: float | int,
        power: float | int,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        wl_interp: bool = False,
        timeout_s: float | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        self.init_params = {
            "target_wavelength": target_wavelength,
            "power": power,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
            "timeout_s": timeout_s,
        }
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    @property
    def linewidth(self):
        """Laser linewidth (device-specific units)."""
        return self.get_property("linewidth")

    @linewidth.setter
    def linewidth(self, value: int) -> None:
        self.set_property("linewidth", value)


class AgilentLaserClient(TunableLaserClientBase, PowerSettable, OSATuningClientMixin):
    """Client for Agilent tunable laser.

    Server-side driver: `devices.laser_control.AgilentLaser`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `agilent_laser_1`).
        target_wavelength: Initial wavelength (nm).
        power: Initial output power (device units; see driver docs).
        source: Source channel index for multi-source units (e.g., 1 or 2).
        GPIB_address: Optional override for GPIB address.
        GPIB_bus: Optional override for GPIB bus.
        wl_interp: If true, use interpolation for wavelength moves where supported.
        timeout_s: Transport timeout in seconds.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

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
        timeout_s: float | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        self.init_params = {
            "target_wavelength": target_wavelength,
            "power": power,
            "source": source,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "wl_interp": wl_interp,
            "timeout_s": timeout_s,
        }
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    @property
    def source(self):
        """Active source channel index (int)."""
        return self.get_property("source")

    @source.setter
    def source(self, value: int) -> None:
        self.set_property("source", value)

    @property
    def unit(self):
        """Power unit string (device-dependent)."""
        return self.get_property("unit")

    @unit.setter
    def unit(self, value: str) -> None:
        self.set_property("unit", value)


class PhotoneticsLaserClient(
    TunableLaserClientBase, PowerSettable, OSATuningClientMixin
):
    """Client for Photonetics tunable laser.

    Server-side driver: `devices.laser_control.PhotoneticsLaser`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `photonetics_laser_1`).
        target_wavelength: Initial wavelength (nm).
        power: Initial output power (device units; see driver docs).
        GPIB_address: GPIB address for the laser.
        GPIB_bus: GPIB bus index (defaults to 0).
        unit: Power unit string accepted by the driver (`DBM` or `MW`).
        timeout_s: Transport timeout in seconds.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        target_wavelength: float | int,
        power: float | int,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        unit: str = "DBM",
        timeout_s: float | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        self.init_params = {
            "target_wavelength": target_wavelength,
            "power": power,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "unit": unit,
            "timeout_s": timeout_s,
        }
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    @property
    def power_unit(self) -> str:
        """Set output power unit (`DBM` or `MW`)."""
        return self.get_property("power_unit")

    @power_unit.setter
    def power_unit(self, unit: str = "DBM") -> None:
        """Set output power unit (`DBM` or `MW`)."""
        self.set_property("power_unit", value=unit)


class TiSapphireClient(LabDeviceClient, OSATuningClientMixin):
    """Client for Ti:Sapphire laser.

    Server-side driver: `devices.tisa_control.TiSapphire`.

    Args:
        base_url: Base HTTP URL of the server.
        device_name: Device key from server config (e.g., `tisa`).
        com_port: Serial port index or number.
        NSL: Device step parameter (left steps).
        PSL: Device step parameter (right steps).
        smc_path: Optional path to vendor executable.
        calibration_path: Path to store/load wavelength calibration.
        initial_wavelength: Seed wavelength for open-loop mode.
        nm_to_pos_slope: Fixed slope for open-loop mode (pos/nm).
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

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
        debug: bool = False,
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
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    @property
    def wavelength(self) -> float:
        """Current emission wavelength in nm.

        Notes:
            - If a calibration has been created via `calibrate`, the server
              performs an absolute move using the position↔wavelength map.
            - Without a calibration, the server uses open‑loop behavior seeded by
              an initial wavelength and a fixed nm→position slope.
        """
        return self.get_property("wavelength")

    @wavelength.setter
    def wavelength(self, value: float | int) -> None:
        self.set_property("wavelength", value)

    def delta_wl_nm(self, value: float) -> None:
        """Open-loop relative wavelength step in nm (uses calibration or fixed slope)."""
        self.call("delta_wl_nm", delta_nm=value)

    def delta_wl_arb(self, value: float) -> None:
        """Relative move in actuator units (arbitrary)."""
        self.call("delta_wl_arb", delta_pos=value)

    def get_pos(self) -> float:
        """Return current actuator position."""
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
        """Create a wavelength calibration using an OSA and save it.

        The server sweeps the OSA over a sliding window across
        ``[cal_start, cal_end]`` while stepping the Ti:Sapphire in
        ``cal_step`` nm increments. It records the actuator position and the
        peak wavelength at each step, then saves a position↔wavelength map
        used for subsequent absolute wavelength moves.

        Args:
            osa: OSA client used for peak detection.
            cal_start: Start wavelength in nm.
            cal_end: End wavelength in nm.
            cal_step: Wavelength increment in nm (> 0 and < ``padding``).
            interval: OSA window width in nm for local scans.
            padding: Guard band in nm around the local scan window.
            res: OSA resolution bandwidth in nm.
        """
        self.call(
            "calibrate",
            osa_device=osa.device_name,
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
        """Iteratively tune to ``target_wl`` using OSA feedback.

        The server repeatedly narrows in on the target wavelength by sweeping
        the OSA, locating the spectral peak, and adjusting the actuator until
        the absolute error is below ``error_tolerance``.

        Args:
            target_wl: Target wavelength in nm.
            osa: OSA client used for feedback.
            min_peak_val: Minimum acceptable peak (dBm) to consider a valid hit.
            osa_rough_res: OSA RBW in nm for initial coarse search.
            osa_fine_res: OSA RBW in nm for fine approach.
            error_tolerance: Stop when absolute wavelength error < tolerance (nm).
        """
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
        self.disconnect()


class VerdiLaserClient(LabDeviceClient):
    """Client for Coherent Verdi laser.

    Server-side driver: `devices.verdi_laser.VerdiLaser`.

    Args:
        base_url: Base HTTP URL of the server.
        device_name: Device key from server config (e.g., `verdi`).
        com_port: Serial port index for RS-232.
        baudrate: Serial baud rate.
        bytesize: Serial byte size.
        stopbits: Serial stop bits.
        timeout_s: Serial timeout (seconds).
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        com_port: int | None = None,
        baudrate: int = 19200,
        bytesize: int = 8,
        stopbits: int = 1,
        timeout_s: int = 2,
        user: str | None = None,
        debug: bool = False,
    ):
        self.init_params = {
            "com_port": com_port,
            "baudrate": baudrate,
            "bytesize": bytesize,
            "stopbits": stopbits,
            "timeout_s": timeout_s,
        }
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    def port_pause(self) -> None:
        """Pause serial port (driver-specific)."""
        self.call("port_pause")

    def port_clear(self) -> None:
        """Clear serial port buffers (driver-specific)."""
        self.call("port_clear")

    def port_close(self) -> None:
        """Close the laser’s serial port (driver-specific)."""
        self.call("port_close")

    def laser_home(self) -> None:
        """Home the laser (driver-specific)."""
        self.call("laser_home")

    def in_waiting(self) -> None:
        """Return/clear input waiting status (driver-specific)."""
        self.call("in_waiting")

    def laser_query(self) -> None:
        """Send a low-level laser query (driver-specific)."""
        self.call("laser_query")

    def shutdown(self) -> None:
        """Gracefully shut down the laser (driver-specific)."""
        self.call("shutdown")

    def standby_on(self) -> None:
        """Enable standby mode."""
        self.call("standby_on")

    def active_on(self) -> None:
        """Enable active (output) mode."""
        self.call("active_on")

    def close(self) -> None:
        self.disconnect()

    @property
    def shutter(self):
        """Shutter state (property)."""
        return self.get_property("shutter")

    @shutter.setter
    def shutter(self, value: int) -> None:
        self.set_property("shutter", value)

    @property
    def power(self):
        """Output power (property)."""
        return self.get_property("power")

    @power.setter
    def power(self, value: float | int) -> None:
        self.set_property("power", value)


if __name__ == "__main__":
    ip = "http://100.80.226.33:5000"
    agilent1 = AgilentLaserClient(ip, "agilent_laser", 1551, power=0, source=1)
    agilent2 = AgilentLaserClient(ip, "agilent_laser", 1551, power=0, source=2)
