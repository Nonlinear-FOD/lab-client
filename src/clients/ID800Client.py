from .base_client import LabDeviceClient
import numpy as np


class ID800Client(LabDeviceClient):
    """Client for ID Quantique ID800 Time Tagger.

    Server-side driver: `devices.ID800_class.ID800`.

    Args:
        base_url: Base HTTP URL of the server (e.g., `http://127.0.0.1:5000`).
        device_name: Device key from server config (e.g., `ID800_1`).
        dll_path: Optional path to the DLL.
        timestamp_count: Number of timestamps in internal buffer.
        channels_enabled: Mask for enabled channels (0xFF for all 8 channels).
        exposure_time_ms: Exposure time for start/stop or histogram operations.
        coincidence_window_bins: Coincidence window in bins.
        auto_connect: Automatically connect on initialization.
        user: Optional user name for server-side locking.
        debug: When True, server returns detailed error payloads.
    """

    def __init__(
        self,
        base_url: str,
        device_name: str,
        dll_path: str | None = None,
        timestamp_count: int | None = None,
        channels_enabled: int | None = None,
        exposure_time_ms: int | None = None,
        coincidence_window_bins: int | None = None,
        auto_connect: bool = True,
        user: str | None = None,
        debug: bool = False,
    ):
        init_params = {
            "dll_path": dll_path,
            "timestamp_count": timestamp_count,
            "channels_enabled": channels_enabled,
            "exposure_time_ms": exposure_time_ms,
            "coincidence_window_bins": coincidence_window_bins,
            "auto_connect": auto_connect,
        }
        # remove None values
        self.init_params = {k: v for k, v in init_params.items() if v is not None}
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(self.init_params)

    # -------------------- connection --------------------
    def connect(self) -> None:
        self.call("connect")

    def close(self) -> None:
        self.call("close")

    @property
    def connected(self) -> bool:
        return self.get_property("connected")

    # -------------------- timestamps --------------------
    def get_last_timestamps(self, reset: bool = False) -> tuple[np.ndarray, np.ndarray, int]:
        """Return (timestamps, channels, valid_count)."""
        return self.call("get_last_timestamps", reset=reset)

    def write_timestamps_to_file(self, filename: str, fileformat: int = 1) -> None:
        self.call("write_timestamps_to_file", filename=filename, fileformat=fileformat)

    def get_data_lost(self) -> int:
        return self.call("get_data_lost")

    # -------------------- histogram / coincidence --------------------
    def enable_start_stop(self, enable: bool = True) -> None:
        self.call("enable_start_stop", enable=enable)

    def set_histogram_params(self, bin_width: int, bin_count: int) -> None:
        self.call("set_histogram_params", bin_width=bin_width, bin_count=bin_count)

    def add_histogram(self, start_channel: int, stop_channel: int, add: bool = True) -> None:
        self.call("add_histogram", start_channel=start_channel, stop_channel=stop_channel, add=add)

    def clear_all_histograms(self) -> None:
        self.call("clear_all_histograms")

    def get_histogram(self, ch_start: int = -1, ch_stop: int = -1, reset: bool = False):
        return self.call("get_histogram", ch_start=ch_start, ch_stop=ch_stop, reset=reset)

    def get_coinc_counters(self) -> tuple[np.ndarray, int]:
        return self.call("get_coinc_counters")

    # -------------------- channel delays --------------------
    def get_channel_delay(self) -> tuple[int, np.ndarray]:
        return self.call("get_channel_delay")

    def set_channel_delay(self, channel: int, delay_ps: int) -> None:
        self.call("set_channel_delay", channel=channel, delay_ps=delay_ps)

    # -------------------- properties --------------------
    @property
    def channels_enabled(self) -> int:
        return self.get_property("channels_enabled")

    @channels_enabled.setter
    def channels_enabled(self, value: int) -> None:
        self.set_property("channels_enabled", value)

    @property
    def exposure_time(self) -> int:
        return self.get_property("exposure_time")

    @exposure_time.setter
    def exposure_time(self, ms: int) -> None:
        self.set_property("exposure_time", ms)

    @property
    def coincidence_window(self) -> int:
        return self.get_property("coincidence_window")

    def set_coincidence_window(self, bins: int) -> None:
        self.call("set_coincidence_window", window_bins=bins)

    @property
    def timebase(self) -> float | None:
        return self.get_property("timebase")

    def switch_termination(self, on: bool = True) -> None:
        self.call("switch_termination", on=on)

    def get_version(self) -> float | None:
        return self.call("get_version")
