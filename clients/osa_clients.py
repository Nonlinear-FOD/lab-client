from .base_client import LabDeviceClient
import numpy as np


class OSAClient(LabDeviceClient):
    # TODO: Add a docstring
    def __init__(
        self,
        base_url: str,
        device_name: str,
        span: float | int | tuple[float | int, float | int],
        resolution: float | None = None,
        sensitivity: str | None = None,
        sweeptype: str | None = None,
        trace: str | None = None,
        samples: int | None = None,
        GPIB_address: int | None = None,
        GPIB_bus: int | None = None,
        zero_nm_sweeptime: int | None = None,
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
        }
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name)
        self._initialize_device(self.init_params)

    @property
    def sweeptype(self) -> str:
        return self.get_property("sweeptype")

    @sweeptype.setter
    def sweeptype(self, value: str) -> None:
        self.set_property("sweeptype", value)

    @property
    def resolution(self) -> float:
        return self.get_property("resolution")

    @resolution.setter
    def resolution(self, value: float) -> None:
        self.set_property("resolution", value)

    @property
    def samples(self) -> int | str:
        return self.get_property("samples")

    @samples.setter
    def samples(self, value: int) -> None:
        self.set_property("samples", value)

    @property
    def sensitivity(self) -> str:
        return self.get_property("sensitivity")

    @sensitivity.setter
    def sensitivity(self, value: str) -> None:
        self.set_property("sensitivity", value)

    @property
    def span(self) -> float | int | tuple[float | int, float | int]:
        return self.get_property("span")

    @span.setter
    def span(self, value: float | int | tuple[float | int, float | int]) -> None:
        self.set_property("span", value)

    @property
    def level(self) -> int:
        return self.get_property("level")

    @level.setter
    def level(self, value: int) -> None:
        self.set_property("level", value)

    @property
    def level_scale(self) -> int:
        return self.get_property("level_scale")

    @level_scale.setter
    def level_scale(self, value: int) -> None:
        self.set_property("level_scale", value)

    @property
    def TLS(self) -> bool:
        return self.get_property("TLS")

    @TLS.setter
    def TLS(self, value: bool) -> None:
        self.set_property("TLS", value)

    @property
    def wavelengths(self) -> np.ndarray:
        return np.array(self.get_property("wavelengths"))

    @property
    def powers(self) -> np.ndarray:
        return np.array(self.get_property("powers"))

    @property
    def trace(self) -> str:
        return self.get_property("trace")

    @trace.setter
    def trace(self, value: str) -> None:
        self.set_property("trace", value)

    def write(self, command: str) -> None:
        self.call("write", command=command)

    def query(self, command: str) -> str:
        return self.call("query", command=command)

    @property
    def zero_nm_sweeptime(self) -> int:
        return self.get_property("zero_nm_sweeptime")

    @zero_nm_sweeptime.setter
    def zero_nm_sweeptime(self, value: int) -> None:
        self.set_property("zero_nm_sweeptime", value)

    @property
    def average(self) -> int:
        return self.get_property("average")

    @average.setter
    def average(self, value: int) -> None:
        self.set_property("average", value)

    def fix_trace(self, trace: str | None = None) -> None:
        # Omit the field entirely when None so the server uses the default
        if trace is None:
            self.call("fix_trace")
        else:
            self.call("fix_trace", trace=trace)

    def write_trace(self, trace: str) -> None:
        self.call("write_trace", trace=trace)

    def display_trace(self, trace: str | None = None) -> None:
        if trace is None:
            self.call("display_trace")
        else:
            self.call("display_trace", trace=trace)

    def blank_trace(self, trace: str | None = None) -> None:
        if trace is None:
            self.call("blank_trace")
        else:
            self.call("blank_trace", trace=trace)

    def subtract_to_C(
        self,
        trace1: str = "A",
        trace2: str = "B",
    ) -> None:
        self.call("subtract_to_C", trace1=trace1, trace2=trace2)

    def stop_sweep(self) -> None:
        self.call("stop_sweep")

    def sweep(self) -> None:
        self.call("sweep")

    def update_spectrum(self) -> None:
        self.call("update_spectrum")

    def save(self, filename: str) -> None:
        self.call("save", filename=filename)

    def set_power_marker(self, marker: int, power: float) -> None:
        self.call("set_power_marker", marker=marker, power=power)

    def set_wavelength_marker(self, marker: int, wavelength: float) -> None:
        self.call("set_wavelength_marker", marker=marker, wavelength=wavelength)

    def close(self) -> None:
        self.call("close")

    def __del__(self) -> None:
        self.stop_sweep()
        self.close()
