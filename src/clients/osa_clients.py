from .base_client import LabDeviceClient
import numpy as np


class OSAClient(LabDeviceClient):
    """Client for Ando Optical Spectrum Analyzer.

    Server-side driver: `devices.osa_control.OSA`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `osa_1`).
        span: Initial sweep span in nm. Provide center value or `(start, stop)`.
        resolution: Resolution bandwidth in nm (e.g., 0.05).
        sensitivity: One of the server-configured modes (e.g., `SNORM`, `SMID`, `SHI1`...).
        sweeptype: `"SGL"` for single or `"RPT"` for repeated sweeps.
        trace: Active trace letter (`"A"`, `"B"`, `"C"`).
        samples: Number of points per sweep (device dependent).
        GPIB_address: Optional override for GPIB address.
        GPIB_bus: Optional override for GPIB bus.
        zero_nm_sweeptime: Device-specific time for zero-nm moves.
        timeout_s: Transport timeout in seconds.
        user: Optional user name for server-side locking.
        debug: When true, server returns detailed error payloads.

    Notes:
        - Call `.sweep()` before reading `wavelengths`/`powers`.
        - `.close()` delegates to `.disconnect()` to drop the server instance and release the lock.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        span: float | tuple[float, float],
        resolution: float | None = None,
        sensitivity: str | None = None,
        sweeptype: str | None = None,
        trace: str | None = None,
        samples: int | None = None,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        zero_nm_sweeptime: int | None = None,
        timeout_s: float | None = None,
        TLS: int | None = None,
        user: str | None = None,
        debug: bool = False,
    ):
        init_params = {
            "span": span,
            "resolution": resolution,
            "sensitivity": sensitivity,
            "sweeptype": sweeptype,
            "trace": trace,
            "samples": samples,
            "GPIB_address": GPIB_address,
            "GPIB_bus": GPIB_bus,
            "zero_nm_sweeptime": zero_nm_sweeptime,
            "TLS": TLS,
            "timeout_s": timeout_s,
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    @property
    def sweeptype(self) -> str:
        """Sweep mode (`"SGL"` or `"RPT"`)."""
        return self.get_property("sweeptype")

    @sweeptype.setter
    def sweeptype(self, value: str) -> None:
        self.set_property("sweeptype", value)

    @property
    def resolution(self) -> float:
        """Resolution bandwidth in nm."""
        return self.get_property("resolution")

    @resolution.setter
    def resolution(self, value: float) -> None:
        self.set_property("resolution", value)

    @property
    def samples(self) -> int:
        """Number of samples/points per sweep. 0 sets it to `AUTO`."""
        return self.get_property("samples")

    @samples.setter
    def samples(self, value: int) -> None:
        self.set_property("samples", value)

    @property
    def sensitivity(self) -> str:
        """Detector sensitivity (e.g., `SNORM`, `SMID`, `SHI1`, `SHI2`, `SHI3`)."""
        return self.get_property("sensitivity")

    @sensitivity.setter
    def sensitivity(self, value: str) -> None:
        self.set_property("sensitivity", value)

    @property
    def span(self) -> float | tuple[float, float]:
        """Sweep span in nm. Either a single center value or `(start, stop)`."""
        return self.get_property("span")

    @span.setter
    def span(self, value: float | tuple[float, float]) -> None:
        self.set_property("span", value)

    @property
    def level(self) -> int:
        """Vertical reference level (dB)."""
        return self.get_property("level")

    @level.setter
    def level(self, value: int) -> None:
        self.set_property("level", value)

    @property
    def level_scale(self) -> int:
        """Vertical scale/division (dB)."""
        return self.get_property("level_scale")

    @level_scale.setter
    def level_scale(self, value: int) -> None:
        self.set_property("level_scale", value)

    @property
    def TLS(self) -> bool:
        """Whether the OSA’s TLS mode is enabled (if supported)."""
        return self.get_property("TLS")

    @TLS.setter
    def TLS(self, value: bool) -> None:
        self.set_property("TLS", value)

    @property
    def wavelengths(self) -> np.ndarray:
        """Last sweep wavelengths (nm). Call `.sweep()` first."""
        return np.array(self.get_property("wavelengths"))

    @property
    def powers(self) -> np.ndarray:
        """Last sweep powers (dBm or device units). Call `.sweep()` first."""
        return np.array(self.get_property("powers"))

    @property
    def trace(self) -> str:
        """Active trace letter (`"A"`, `"B"`, `"C"`)."""
        return self.get_property("trace")

    @trace.setter
    def trace(self, value: str) -> None:
        self.set_property("trace", value)

    def write(self, command: str) -> None:
        """Send a raw SCPI/text command to the OSA."""
        self.call("write", command=command)

    def query(self, command: str) -> str:
        """Send a raw query command and return the string response."""
        return self.call("query", command=command)

    @property
    def zero_nm_sweeptime(self) -> int:
        """Device-specific sweep time for zero-nm moves (s)."""
        return self.get_property("zero_nm_sweeptime")

    @zero_nm_sweeptime.setter
    def zero_nm_sweeptime(self, value: int) -> None:
        self.set_property("zero_nm_sweeptime", value)

    @property
    def average(self) -> int:
        """Trace averaging count (device dependent)."""
        return self.get_property("average")

    @average.setter
    def average(self, value: int) -> None:
        self.set_property("average", value)

    def fix_trace(self, trace: str | None = None) -> None:
        """Make the given trace active and writable on the display."""
        # Omit the field entirely when None so the server uses the default
        if trace is None:
            self.call("fix_trace")
        else:
            self.call("fix_trace", trace=trace)

    def write_trace(self, trace: str) -> None:
        """Set the active trace to `trace` without changing visibility."""
        self.call("write_trace", trace=trace)

    def display_trace(self, trace: str | None = None) -> None:
        """Show the given trace (or current) on the display."""
        if trace is None:
            self.call("display_trace")
        else:
            self.call("display_trace", trace=trace)

    def blank_trace(self, trace: str | None = None) -> None:
        """Hide the given trace (or current) from the display."""
        if trace is None:
            self.call("blank_trace")
        else:
            self.call("blank_trace", trace=trace)

    def subtract_to_C(
        self,
        trace1: str = "A",
        trace2: str = "B",
    ) -> None:
        """Subtract trace2 from trace1 and store in C."""
        self.call("subtract_to_C", trace1=trace1, trace2=trace2)

    def stop_sweep(self) -> None:
        """Stop any ongoing sweep."""
        self.call("stop_sweep")

    def sweep(self) -> None:
        """Trigger a sweep with current settings. Updates `wavelengths/powers` if `sweeptype` is `SGL`."""
        self.call("sweep")

    def update_spectrum(self) -> None:
        """Refresh display/spectrum with current settings (no configuration changes)."""
        self.call("update_spectrum")

    def set_power_marker(self, marker: int, power: float) -> None:
        """Place a power marker at the given value on the active trace."""
        self.call("set_power_marker", marker=marker, power=power)

    def set_wavelength_marker(self, marker: int, wavelength: float) -> None:
        """Place a wavelength marker at the given position on the active trace."""
        self.call("set_wavelength_marker", marker=marker, wavelength=wavelength)

    def close(self) -> None:
        """Release server-side instance and lock (delegates to `.disconnect()`)."""
        self.disconnect()
