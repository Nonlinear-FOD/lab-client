from __future__ import annotations

from typing import Sequence, Any
from enum import IntEnum

import numpy as np

from clients.base_client import LabDeviceClient


# ---------------- Convenience enums/constants ----------------
class WaveType(IntEnum):
    """PicoSDK built-in generator wave types (common values).

    Values reflect typical PS2000A assignments; verify with your SDK if needed.
    """

    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    RAMP_UP = 3
    RAMP_DOWN = 4
    SINC = 5
    GAUSSIAN = 6
    HALF_SINE = 7


class Coupling(IntEnum):
    """Channel coupling types."""

    AC = 0
    DC = 1


class Range(IntEnum):
    """Input voltage ranges (PicoSDK PS2000A_RANGE enum).

    These integer codes determine the scaling used by the SDK to convert ADC
    counts to millivolts. Default used in our server driver is ``Range.V1`` (6).
    """

    MV10 = 0
    MV20 = 1
    MV50 = 2
    MV100 = 3
    MV200 = 4
    MV500 = 5
    V1 = 6
    V2 = 7
    V5 = 8
    V10 = 9
    V20 = 10


class Direction(IntEnum):
    """Trigger direction for scope edge trigger (PS2000A)."""

    ABOVE = 0
    BELOW = 1
    RISING = 2
    FALLING = 3
    RISING_OR_FALLING = 4


class RatioMode(IntEnum):
    """Downsampling ratio modes (PS2000A_RATIO_MODE)."""

    NONE = 0
    AGGREGATE = 1
    DECIMATE = 2
    AVERAGE = 4


class PicoScope2000AClient(LabDeviceClient):
    """Client for PicoScope 2000A oscilloscope and AWG.

    Maps 1:1 to the server driver ``devices.picoscope2000a.PicoScope2000A`` and
    exposes methods for AWG control and block capture. Use in this order:

    1) ``scope_configure_channel`` to set up the input range and coupling.
    2) ``scope_configure_trigger`` to align acquisition (or disable for free‑run).
    3) ``scope_capture`` to acquire time and mV arrays.

    Notes:
        - Triggers control when the capture starts, not signal shape. If you just
          need a snapshot, disable the trigger or set ``auto_trigger_ms`` > 0.
        - Current server implementation captures one channel per call. To measure
          both A and B, disable A before enabling B, then capture again.
        - Enums are exposed on the client: ``pico.WaveType``, ``pico.Coupling``,
          ``pico.Range``, ``pico.Direction``, ``pico.RatioMode``.
    """

    # Expose enums as attributes so users can access via instance/class
    WaveType = WaveType
    Coupling = Coupling
    Range = Range
    Direction = Direction
    RatioMode = RatioMode

    def __init__(
        self,
        base_url: str,
        device_name: str,
        serial: str | None = None,
        user: str | None = None,
        debug: bool = False,
    ) -> None:
        """Create and connect a PicoScope2000A session on the server.

        Args:
            base_url: FastAPI server base URL (e.g., ``http://127.0.0.1:5000``).
            device_name: Name/key of the device in server config (e.g., ``picoscope2000a``).
            serial: Optional Pico unit serial. If ``None``, opens first available unit.
            user: Optional user name for server-side locking.
            debug: Include detailed error traces from server if ``True``.
        """
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device({"serial": serial})

    @staticmethod
    def _enum_dict(E: type[IntEnum]) -> dict[str, int]:
        return {name: int(val) for name, val in E.__members__.items()}

    def list_options(self) -> dict[str, dict[str, int]]:
        """Return available enum options for discoverability.

        Keys: 'WaveType', 'Coupling', 'Range', 'Direction', 'RatioMode'.
        Values: mapping of member name -> integer value.
        """
        return {
            "WaveType": self._enum_dict(self.WaveType),
            "Coupling": self._enum_dict(self.Coupling),
            "Range": self._enum_dict(self.Range),
            "Direction": self._enum_dict(self.Direction),
            "RatioMode": self._enum_dict(self.RatioMode),
        }

    def print_options(self) -> None:
        """Pretty-print enum names and values."""
        for group, members in self.list_options().items():
            print(f"{group}:")
            for name, val in members.items():
                print(f"  - {name} = {val}")

    # ---------------------- AWG ----------------------
    def awg_set_builtin(
        self,
        wave_type: int | WaveType,
        frequency: float | Sequence[float],
        pk_to_pk_uv: int = 2_000_000,
        offset_uv: int = 0,
        increment_hz: float = 0.0,
        dwell_time_s: float = 1.0,
        sweep_type: int = 0,
        operation: int = 0,
        shots: int = 0,
        sweeps: int = 0,
        trigger_type: int = 0,
        trigger_source: int = 0,
        ext_in_threshold_mv: int = 1,
    ) -> None:
        """Configure the built-in signal generator.

        Args:
            wave_type: Built-in waveform type (``WaveType`` or int).
            frequency: Output frequency in Hz. Scalar for steady output or pair ``(start, stop)`` for sweep.
            pk_to_pk_uv: Peak-to-peak amplitude in microvolts. Defaults to 2,000,000 (2 Vpp).
            offset_uv: DC offset in microvolts. Defaults to 0.
            increment_hz: Frequency step during sweep. Defaults to 0.0.
            dwell_time_s: Time per step (s) in sweep mode. Defaults to 1.0.
            sweep_type: PicoSDK sweep enum (int).
            operation: PicoSDK operation (single/continuous) (int).
            shots: Number of bursts (if applicable).
            sweeps: Number of sweeps (if applicable).
            trigger_type: Siggen trigger type (int).
            trigger_source: Siggen trigger source (int).
            ext_in_threshold_mv: External trigger threshold (mV).

        Notes:
            Mirrors the server method ``PicoScope2000A.awg_set_builtin``.
        """
        self.call(
            "awg_set_builtin",
            wave_type=int(wave_type),
            frequency=frequency,
            pk_to_pk_uv=pk_to_pk_uv,
            offset_uv=offset_uv,
            increment_hz=increment_hz,
            dwell_time_s=dwell_time_s,
            sweep_type=sweep_type,
            operation=operation,
            shots=shots,
            sweeps=sweeps,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            ext_in_threshold_mv=ext_in_threshold_mv,
        )

    def awg_set_arbitrary(
        self,
        frequency: float | Sequence[float],
        waveform: Sequence[int],
        pk_to_pk_uv: int = 2_000_000,
        offset_uv: int = 0,
        delta_phase_increment: int = 0,
        dwell_count: int = 0,
        sweep_type: int = 0,
        operation: int = 0,
        index_mode: int = 0,
        shots: int = 0,
        sweeps: int = 0,
        trigger_type: int = 0,
        trigger_source: int = 0,
        ext_in_threshold_mv: int = 1,
    ) -> None:
        """Configure the arbitrary waveform generator (AWG).

        Args:
            frequency: Output frequency in Hz. Scalar or pair ``(start, stop)`` for a sweep.
            waveform: Int16-compatible samples in [-32768, 32767].
            pk_to_pk_uv: Peak-to-peak amplitude in microvolts.
            offset_uv: DC offset in microvolts.
            delta_phase_increment: DDS delta-phase increment for sweep.
            dwell_count: Cycles per delta-phase step in sweep.
            sweep_type: PicoSDK sweep enum (int).
            operation: PicoSDK operation (single/continuous) (int).
            index_mode: PicoSDK index mode (int).
            shots: Number of bursts (if applicable).
            sweeps: Number of sweeps (if applicable).
            trigger_type: Siggen trigger type (int).
            trigger_source: Siggen trigger source (int).
            ext_in_threshold_mv: External trigger threshold (mV).

        Notes:
            Mirrors the server method ``PicoScope2000A.awg_set_arbitrary``.
        """
        self.call(
            "awg_set_arbitrary",
            frequency=frequency,
            waveform=list(int(x) for x in waveform),
            pk_to_pk_uv=pk_to_pk_uv,
            offset_uv=offset_uv,
            delta_phase_increment=delta_phase_increment,
            dwell_count=dwell_count,
            sweep_type=sweep_type,
            operation=operation,
            index_mode=index_mode,
            shots=shots,
            sweeps=sweeps,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            ext_in_threshold_mv=ext_in_threshold_mv,
        )

    def awg_square_duty(
        self,
        frequency: float,
        duty_cycle: float,
        waveform_size: int = 2**12,
        pk_to_pk_uv: int = 2_000_000,
        offset_uv: int = 1_000_000,
    ) -> np.ndarray:
        """Generate and apply a duty-cycle square wave on the AWG.

        Args:
            frequency: Output frequency in Hz.
            duty_cycle: Fraction in [0, 1] (e.g., 0.5 for 50%).
            waveform_size: Number of samples in the arbitrary waveform.
            pk_to_pk_uv: Peak-to-peak amplitude in microvolts.
            offset_uv: DC offset in microvolts.

        Returns:
            np.ndarray: Int16 waveform used (shape=(waveform_size,)).
        """
        wf = self.call(
            "awg_square_duty",
            frequency=frequency,
            duty_cycle=float(duty_cycle),
            waveform_size=int(waveform_size),
            pk_to_pk_uv=int(pk_to_pk_uv),
            offset_uv=int(offset_uv),
        )
        return np.asarray(wf, dtype=np.int16)

    def awg_square_pulse(
        self,
        frequency: float,
        start_frac: float,
        end_frac: float,
        waveform_size: int = 2**12,
        pk_to_pk_uv: int = 2_000_000,
        offset_uv: int = 1_000_000,
    ) -> np.ndarray:
        """Generate and apply a single square pulse on the AWG.

        Args:
            frequency: Output frequency in Hz.
            start_frac: Pulse start fraction [0, 1].
            end_frac: Pulse end fraction [0, 1]; must be >= ``start_frac``.
            waveform_size: Number of samples in the arbitrary waveform.
            pk_to_pk_uv: Peak-to-peak amplitude in microvolts.
            offset_uv: DC offset in microvolts.

        Returns:
            np.ndarray: Int16 waveform used (shape=(waveform_size,)).
        """
        wf = self.call(
            "awg_square_pulse",
            frequency=frequency,
            start_frac=float(start_frac),
            end_frac=float(end_frac),
            waveform_size=int(waveform_size),
            pk_to_pk_uv=int(pk_to_pk_uv),
            offset_uv=int(offset_uv),
        )
        return np.asarray(wf, dtype=np.int16)

    # ---------------------- Scope ----------------------
    def scope_configure_channel(
        self,
        channel: int = 0,
        enabled: bool = True,
        coupling_type: int | Coupling = 1,
        channel_range: int | Range = 6,
        analogue_offset: float = 0.0,
    ) -> None:
        """Configure acquisition channel (server-side).

        Args:
            channel: 0 for channel A, 1 for channel B.
            enabled: Enable/disable the input.
            coupling_type: 1=DC, 0=AC (``Coupling`` or int).
            channel_range: Input range enum (``Range`` or int). Determines ADC→mV scaling.
            analogue_offset: Offset voltage in volts.
        """
        self.call(
            "scope_configure_channel",
            channel=int(channel),
            enabled=bool(enabled),
            coupling_type=int(coupling_type),
            channel_range=int(channel_range),
            analogue_offset=float(analogue_offset),
        )

    def scope_configure_trigger(
        self,
        enabled: bool = True,
        source_channel: int | None = None,
        threshold_adc: int = 1024,
        threshold_mv: float | None = None,
        direction: int | Direction = 0,
        delay: int = 0,
        auto_trigger_ms: int = 100,
    ) -> None:
        """Configure simple edge trigger (server-side).

        Args:
            enabled: Enable/disable triggering.
            source_channel: 0=A, 1=B. If ``None``, uses the last configured channel.
            threshold_adc: Raw trigger level in ADC counts (used when ``threshold_mv`` is ``None``).
            threshold_mv: Trigger level in millivolts. If provided, overrides ``threshold_adc``.
            direction: Edge direction (``Direction`` or int).
            delay: Delay (samples) from the trigger point.
            auto_trigger_ms: Auto-trigger fallback in milliseconds (0 disables fallback).

        Notes:
            For quick snapshots, set ``enabled=False`` or keep ``auto_trigger_ms`` > 0.
            To align consistently on an edge, set ``auto_trigger_ms=0`` and choose a level with a single crossing.
        """
        payload: dict[str, Any] = {
            "enabled": bool(enabled),
            "direction": int(direction),
            "delay": int(delay),
            "auto_trigger_ms": int(auto_trigger_ms),
        }
        if source_channel is not None:
            payload["source_channel"] = int(source_channel)
        if threshold_mv is not None:
            payload["threshold_mv"] = float(threshold_mv)
        else:
            payload["threshold_adc"] = int(threshold_adc)
        self.call("scope_configure_trigger", **payload)

    def scope_capture(
        self,
        num_samples: int,
        timebase: int = 8,
        oversample: int = 0,
        pre_trigger: int | None = None,
        post_trigger: int | None = None,
        downsample_ratio: int = 0,
        downsample_mode: int = 0,
        ratio_mode: int = 0,
    ) -> dict:
        """Run a block capture and return arrays.

        Args:
            num_samples: Total samples to acquire (pre + post).
            timebase: PicoSDK timebase index; actual interval is resolved server-side.
            oversample: Hardware oversampling factor.
            pre_trigger: Samples before the trigger (defaults to half).
            post_trigger: Samples after the trigger (defaults to remainder).
            downsample_ratio: Downsampling ratio.
            downsample_mode: Downsampling mode.
            ratio_mode: Ratio mode for data buffers.

        Returns:
            dict: Keys ``time_us`` (np.ndarray), ``mV`` (np.ndarray), ``overflow`` (int),
            ``maxADC`` (int), and ``samples`` (int).

        Notes:
            The server currently captures one channel per call. To measure both A and B, disable A before enabling B and run two captures.
        """
        payload: dict[str, Any] = {
            "num_samples": int(num_samples),
            "timebase": int(timebase),
            "oversample": int(oversample),
            "downsample_ratio": int(downsample_ratio),
            "downsample_mode": int(downsample_mode),
            "ratio_mode": int(ratio_mode),
        }
        if pre_trigger is not None:
            payload["pre_trigger"] = int(pre_trigger)
        if post_trigger is not None:
            payload["post_trigger"] = int(post_trigger)
        out = self.call("scope_capture", **payload)
        # Convert arrays
        out["time_us"] = np.asarray(out["time_us"], dtype=float)
        out["mV"] = np.asarray(out["mV"], dtype=float)
        out["overflow"] = int(out["overflow"])  # type: ignore[index]
        out["maxADC"] = int(out["maxADC"])  # type: ignore[index]
        out["samples"] = int(out["samples"])  # type: ignore[index]
        return out

    def close(self) -> None:
        """Disconnect and release the server-side instance."""
        self.disconnect()
