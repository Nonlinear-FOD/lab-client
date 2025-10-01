"""Long-period grating (LPG) fabrication orchestration helpers.

This module factors the standalone ``testing_client/lpg_test.py`` script into a
reusable API so interactive notebooks or higher-level tooling can import and
compose LPG write/read sequences alongside the existing instrument clients.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from clients.keithley2700_client import Keithley2700Client
from clients.osa_clients import OSAClient
from clients.tenma_psu_client import TenmaPSUClient
from clients.zaber_1d_client import Zaber1DMotorClient

FloatArray = NDArray[np.float64]


@runtime_checkable
class OSAClientProtocol(Protocol):
    @property
    def span(self) -> float | tuple[float, float]: ...

    @span.setter
    def span(self, value: float | tuple[float, float]) -> None: ...

    @property
    def resolution(self) -> float: ...

    @resolution.setter
    def resolution(self, value: float) -> None: ...

    @property
    def sensitivity(self) -> str: ...

    @sensitivity.setter
    def sensitivity(self, value: str) -> None: ...

    @property
    def trace(self) -> str: ...

    @trace.setter
    def trace(self, value: str) -> None: ...

    @property
    def TLS(self) -> bool: ...

    @TLS.setter
    def TLS(self, value: bool) -> None: ...

    def sweep(self) -> None: ...

    def update_spectrum(self) -> None: ...

    @property
    def wavelengths(self) -> FloatArray: ...

    @property
    def powers(self) -> FloatArray: ...


@runtime_checkable
class Zaber1DMotorProtocol(Protocol):
    @property
    def units(self) -> str: ...

    @units.setter
    def units(self, value: str) -> None: ...

    def home(self) -> None: ...

    def move_relative(self, distance: float) -> None: ...


@runtime_checkable
class TenmaPSUProtocol(Protocol):
    @property
    def channel(self) -> int: ...

    @channel.setter
    def channel(self, value: int) -> None: ...

    @property
    def voltage_set(self) -> float: ...

    @voltage_set.setter
    def voltage_set(self, value: float) -> None: ...

    @property
    def current_set(self) -> float: ...

    @current_set.setter
    def current_set(self, value: float) -> None: ...

    @property
    def output(self) -> bool: ...

    @output.setter
    def output(self, enabled: bool) -> None: ...


@runtime_checkable
class Keithley2700Protocol(Protocol):
    def read_voltage(self) -> float: ...


@dataclass
class LPGRunSettings:
    """Runtime parameters controlling an LPG write/read sequence."""

    directory: str = "testing_client/_runs/lpg"
    file_prefix: str = "lpg_demo"
    n_periods: int = 20
    start_period: int = 0
    period_um: float = 450.0
    heat_time_s: float = 5.0
    measure_delay_s: float = 1.0
    sleep_before_scan_s: float = 2.0
    dip_limit_db: float = 10.0
    burn_factor: float = 1.5
    headroom: float | None = None
    fixed_voltage_limit_v: float = 10.0
    wire_power_w: float = 6.2
    wire_res_ohm: float = 0.1494
    osa_span_nm: tuple[float, float] = (1450.0, 1650.0)
    osa_resolution_nm: float = 0.5
    osa_sensitivity: str = "SMID"
    osa_trace: str = "A"
    tension_g: float = 3.5
    home_offset_um: float = 100.0
    stage_units: str = "um"
    comment: str = ""
    psu_type: str = "Tenma"
    measure_reference: bool = True
    reference_path: str | None = None
    plot_stack: bool = True
    zaber_com_port: int | None = None
    psu_com_port: int | None = None
    psu_channel: int = 2

    def __post_init__(self) -> None:
        # JSON loaders may coerce tuples to lists; normalise here.
        if isinstance(self.osa_span_nm, Iterable) and not isinstance(
            self.osa_span_nm, tuple
        ):
            span = list(self.osa_span_nm)
            if len(span) != 2:
                msg = f"osa_span_nm must contain exactly two elements, got {span!r}"
                raise ValueError(msg)
            self.osa_span_nm = (float(span[0]), float(span[1]))
        self.directory = str(self.directory)
        if self.reference_path is not None:
            self.reference_path = str(self.reference_path)
        self.stage_units = str(self.stage_units)
        if self.psu_channel <= 0:
            raise ValueError("psu_channel must be a positive integer")

    @property
    def out_dir(self) -> Path:
        """Directory where spectra/logs are persisted."""
        return Path(self.directory).expanduser()

    def ensure_out_dir(self) -> Path:
        """Create ``out_dir`` if missing and return it."""
        out_dir = self.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    @property
    def resolved_reference_path(self) -> Path:
        """Path to the reference spectrum CSV for this run."""
        if self.reference_path:
            return Path(self.reference_path).expanduser()
        return self.out_dir / f"{self.file_prefix}_reference.csv"

    @property
    def first_series(self) -> str:
        """Return ``"Yes"``/``"No"`` for legacy CSV compatibility."""
        return "Yes" if self.start_period == 0 else "No"

    @property
    def target_current_a(self) -> float:
        """Current (A) required to reach ``wire_power_w``.

        Returns 0.0 when inputs are non-positive to avoid sqrt errors.
        """
        if self.wire_power_w <= 0 or self.wire_res_ohm <= 0:
            return 0.0
        return math.sqrt(self.wire_power_w / self.wire_res_ohm)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable settings dict."""
        data = asdict(self)
        # Ensure tuple survives round-trip.
        data["osa_span_nm"] = list(self.osa_span_nm)
        return data

    def to_json(self, path: str | Path) -> None:
        """Serialise settings to JSON."""
        with Path(path).expanduser().open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def from_json(cls, path: str | Path) -> "LPGRunSettings":
        """Load settings from JSON file."""
        with Path(path).expanduser().open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(**data)


@dataclass
class LPGFabResult:
    """Result container returned by :class:`LPGFab.run`."""

    spectra: FloatArray
    resistances: list[float]
    reference: tuple[FloatArray, FloatArray]
    settings: LPGRunSettings
    periods_written: int
    stop_reason: str | None = None

    @property
    def wavelengths(self) -> FloatArray:
        """Convenience access to the wavelength axis."""
        if self.spectra.size == 0:
            return np.array([], dtype=float)
        return np.asarray(self.spectra[:, 0], dtype=float)


class LPGFabError(RuntimeError):
    """Raised when an unrecoverable LPG sequencing error occurs."""


class LPGFab:
    """High-level coordinator for LPG write/read workflows."""

    def __init__(
        self,
        base_url: str,
        *,
        osa_id: str,
        zaber_id: str,
        psu_id: str,
        dmm_id: str,
        run_settings: LPGRunSettings,
        user: str | None = None,
        debug: bool = False,
        logger: logging.Logger | None = None,
        osa: OSAClientProtocol | None = None,
        zaber: Zaber1DMotorProtocol | None = None,
        psu: TenmaPSUProtocol | None = None,
        dmm: Keithley2700Protocol | None = None,
    ) -> None:
        self.settings = run_settings
        self.logger = logger or self._build_logger()

        if osa is None:
            self.osa = OSAClient(
                base_url,
                osa_id,
                span=run_settings.osa_span_nm,
                resolution=run_settings.osa_resolution_nm,
                sensitivity=run_settings.osa_sensitivity,
                trace=run_settings.osa_trace,
                user=user,
                debug=debug,
            )
        else:
            self.osa = osa

        if zaber is None:
            self.zaber = Zaber1DMotorClient(
                base_url,
                zaber_id,
                com_port=run_settings.zaber_com_port,
                units=run_settings.stage_units,
                user=user,
                debug=debug,
            )
        else:
            self.zaber = zaber

        if psu is None:
            self.psu = TenmaPSUClient(
                base_url,
                psu_id,
                com_port=run_settings.psu_com_port,
                channel=run_settings.psu_channel,
                user=user,
                debug=debug,
            )
        else:
            self.psu = psu

        if dmm is None:
            self.dmm = Keithley2700Client(
                base_url,
                dmm_id,
                user=user,
                debug=debug,
            )
        else:
            self.dmm = dmm

        if self.settings.stage_units:
            self.zaber.units = self.settings.stage_units

        self._tls_on = bool(self.osa.TLS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> LPGFabResult:
        """Execute the configured LPG sequence and return captured data."""
        settings = self.settings
        settings.ensure_out_dir()
        self.logger.info("Configuring OSA")
        self._configure_osa()
        reference = self._prepare_reference()
        resistances: list[float] = []
        periods_written = 0
        stop_reason: str | None = None
        try:
            spec, resistances, start_offset, periods_written, stop_reason = (
                self._execute(reference, resistances)
            )
        finally:
            self._safe_psu_off()
        self.logger.info(f"Finished after {periods_written} periods.")
        return LPGFabResult(
            spectra=spec,
            resistances=resistances,
            reference=reference,
            settings=settings,
            periods_written=periods_written,
            stop_reason=stop_reason,
        )

    def close(self) -> None:
        """Release instrument sessions."""
        for client in (self.osa, self.zaber, self.psu, self.dmm):
            try:
                close = getattr(client, "close", None)
                if callable(close):
                    close()
                else:
                    disconnect = getattr(client, "disconnect", None)
                    if callable(disconnect):
                        disconnect()
            except Exception:
                continue

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_logger(self) -> logging.Logger:
        """Create or reuse the logger used for this Fab run."""
        out_dir = self.settings.ensure_out_dir()
        logger_name = f"lpg.{self.settings.file_prefix}"
        logger = logging.getLogger(logger_name)
        if logger.handlers:
            return logger
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            out_dir / f"{self.settings.file_prefix}_{ts}.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def _configure_osa(self) -> None:
        """Push span, resolution, sensitivity and trace to the OSA client."""
        s = self.settings
        self.osa.span = s.osa_span_nm
        self.osa.resolution = float(s.osa_resolution_nm)
        self.osa.sensitivity = str(s.osa_sensitivity)
        self.osa.trace = str(s.osa_trace)

    def _prepare_reference(self) -> tuple[FloatArray, FloatArray]:
        """Obtain or load the reference spectrum for delta comparisons."""
        s = self.settings
        ref_path = s.resolved_reference_path
        if s.measure_reference:
            self.logger.info("Measuring reference sweep")
            wl, pw = self._sweep_and_check_tls()
            try:
                ref_path.parent.mkdir(parents=True, exist_ok=True)
                np.savetxt(
                    ref_path,
                    np.column_stack([wl, pw]),
                    delimiter=",",
                    fmt="%.6f",
                )
                self.logger.info(f"Saved reference to {ref_path}")
            except Exception:
                self.logger.debug(
                    f"Could not save reference to {ref_path}", exc_info=True
                )
            return wl, pw.copy()

        try:
            ref = np.loadtxt(ref_path, delimiter=",")
        except Exception as exc:
            msg = (
                f"Reference file not found at {ref_path}. Set ``measure_reference=True`` "
                "to capture a fresh spectrum."
            )
            raise LPGFabError(msg) from exc
        wl = np.asarray(ref[:, 0], dtype=float)
        pw = np.asarray(ref[:, 1], dtype=float)
        self.logger.info(f"Loaded reference from {ref_path}")
        return wl, pw

    def _execute(
        self,
        reference: tuple[FloatArray, FloatArray],
        resistances: list[float],
    ) -> tuple[FloatArray, list[float], int, int, str | None]:
        """Main loop that writes periods, collects spectra and tracks stop reasons."""
        settings = self.settings
        current_a = settings.target_current_a
        if current_a <= 0:
            raise LPGFabError(
                "Invalid target current derived from wire_power_w and wire_res_ohm."
            )

        spec, start_offset, periods_written = self._initialise_run(
            reference, current_a, resistances
        )

        stop_reason: str | None = None
        while periods_written < settings.n_periods:
            last_col = np.asarray(spec[:, -1], dtype=float)
            dip_db = float(-np.min(last_col))
            if dip_db > settings.dip_limit_db:
                stop_reason = (
                    f"dip {dip_db:.2f} dB exceeds limit {settings.dip_limit_db:.2f} dB"
                )
                self.logger.info(f"Stopping: {stop_reason}")
                break

            target_period = start_offset + periods_written
            self.logger.info(
                f"Moving stage by {settings.period_um} µm to write period {target_period}"
            )
            self.zaber.move_relative(settings.period_um)

            r = self._heat_and_measure(current_a)
            resistances.append(r)
            if self._burned(r):
                stop_reason = (
                    f"measured R {r:.3f} Ω exceeds {settings.burn_factor:.2f}× initial "
                    f"{settings.wire_res_ohm:.3f} Ω"
                )
                self.logger.info(f"Stopping: {stop_reason}")
                break

            time.sleep(settings.sleep_before_scan_s)
            wl, dp = self._sweep_delta(reference)
            if spec.shape[0] != wl.shape[0]:
                raise LPGFabError("Wavelength grid changed; alignment required.")
            spec = np.column_stack([spec, dp])
            periods_written += 1

            if settings.plot_stack:
                self._plot_stack(spec, start_period=start_offset)
            self.logger.info(f"Written period {target_period}")
            self._save_artifacts(spec, resistances)

        return spec, resistances, start_offset, periods_written, stop_reason

    def _initialise_run(
        self,
        reference: tuple[FloatArray, FloatArray],
        current_a: float,
        resistances: list[float],
    ) -> tuple[FloatArray, int, int]:
        """Build the initial spectra matrix and resume counters."""
        settings = self.settings
        if settings.start_period == 0:
            self.logger.info("Start: baseline scan & slack compensation")
            time.sleep(settings.sleep_before_scan_s)
            wl0, dp0 = self._sweep_delta(reference)
            spec = np.column_stack([wl0, dp0])
            if settings.plot_stack:
                self._plot_stack(spec, start_period=0)

            self.zaber.home()
            if settings.home_offset_um:
                self.zaber.move_relative(settings.home_offset_um)

            r0 = self._heat_and_measure(current_a)
            resistances.append(r0)
            if self._burned(r0):
                raise LPGFabError(
                    f"Measured resistance {r0:.3f} Ω exceeds burn threshold "
                    f"{self._burn_threshold():.3f} Ω"
                )

            time.sleep(settings.sleep_before_scan_s)
            wl1, dp1 = self._sweep_delta(reference)
            spec = np.column_stack([spec, dp1])
            if settings.plot_stack:
                self._plot_stack(spec, start_period=0)
            self.logger.info("Written period 0")
            self._save_artifacts(spec, resistances)
            return spec, 0, 1

        prev = self._load_previous_run()
        if prev is not None:
            spec = prev
            periods_written = int(max(spec.shape[1] - 2, 0))
            if settings.plot_stack:
                self._plot_stack(spec, start_period=0)
            self.logger.info(
                f"Resuming from saved spectra with {periods_written} periods"
            )
            return spec, 0, periods_written

        self.logger.info("Resume (no previous files): move one period and heat")
        self.zaber.move_relative(settings.period_um)
        r0 = self._heat_and_measure(current_a)
        resistances.append(r0)
        if self._burned(r0):
            raise LPGFabError(
                f"Measured resistance {r0:.3f} Ω exceeds burn threshold "
                f"{self._burn_threshold():.3f} Ω"
            )

        time.sleep(settings.sleep_before_scan_s)
        wl1, dp1 = self._sweep_delta(reference)
        spec = np.column_stack([reference[0], dp1])
        if settings.plot_stack:
            self._plot_stack(spec, start_period=settings.start_period)
        self.logger.info(f"Written period {settings.start_period}")
        self._save_artifacts(spec, resistances)
        return spec, settings.start_period, 1

    def _sweep_and_check_tls(self) -> tuple[FloatArray, FloatArray]:
        """Trigger an OSA sweep and return wavelength/power arrays."""
        self.osa.sweep()
        if self._tls_on:
            self.osa.update_spectrum()
        wl = np.asarray(self.osa.wavelengths, dtype=float)
        pw = np.asarray(self.osa.powers, dtype=float)
        return wl, pw

    def _sweep_delta(
        self, reference: tuple[FloatArray, FloatArray]
    ) -> tuple[FloatArray, FloatArray]:
        """Return the current sweep minus the reference powers."""
        wl, pw = self._sweep_and_check_tls()
        ref_wl, ref_pw = reference
        if wl.shape != ref_wl.shape:
            raise LPGFabError(
                "Reference/sweep wavelength grids differ; alignment required."
            )
        delta = pw - ref_pw
        return wl, delta

    def _heat_and_measure(self, current_a: float) -> float:
        """Drive the PSU and report the resulting wire resistance."""
        settings = self.settings
        self.psu.channel = int(settings.psu_channel)
        if settings.headroom is None:
            v_set = settings.fixed_voltage_limit_v
        else:
            v_set = settings.headroom * current_a * settings.wire_res_ohm
        self.psu.voltage_set = float(v_set)
        self.psu.current_set = float(current_a)
        self.psu.output = True
        self.logger.info(
            f"Heating: I_set={current_a:.3f} A, V_set={v_set:.3f} V, t={settings.heat_time_s:.2f}s"
        )
        start = time.perf_counter()
        while time.perf_counter() - start < settings.heat_time_s:
            time.sleep(0.02)
        time.sleep(settings.measure_delay_s)
        v_meas = float(self.dmm.read_voltage())
        self.logger.info(
            f"Measured V={v_meas:.4f} V (delay={settings.measure_delay_s:.2f}s)"
        )
        self.psu.output = False
        if current_a <= 0:
            return float("inf")
        return v_meas / current_a

    def _burn_threshold(self) -> float:
        """Return the burn-out resistance threshold for the current run."""
        return self.settings.burn_factor * self.settings.wire_res_ohm

    def _burned(self, measured_r: float) -> bool:
        """Check whether *measured_r* exceeds the burn threshold."""
        threshold = self._burn_threshold()
        return threshold > 0 and measured_r > threshold

    def _plot_stack(self, spec: FloatArray, *, start_period: int) -> None:
        """Plot stacked spectra columns for quick visual inspection."""
        wl = np.asarray(spec[:, 0], dtype=float)
        plt.figure("LPG spectra")
        plt.clf()
        for idx in range(1, spec.shape[1]):
            if idx == 1:
                label = -1
            else:
                label = start_period + (idx - 2)
            plt.plot(wl, spec[:, idx], label=str(label))
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Power (dB rel. ref)")
        plt.grid(True)
        plt.legend(loc="best", fontsize=8, ncol=2)
        plt.pause(0.01)

    def _save_artifacts(self, spec: FloatArray, resistances: list[float]) -> None:
        """Persist spectra, plots and settings summaries for this run."""
        settings = self.settings
        out_dir = settings.ensure_out_dir()
        prefix = settings.file_prefix
        np.savetxt(out_dir / f"{prefix}_spectra.csv", spec, delimiter=",", fmt="%.6f")
        if settings.plot_stack:
            self._save_plot(out_dir / f"{prefix}_plot.png")
        if resistances:
            try:
                settings.wire_res_ohm = float(np.mean(resistances))
            except Exception:
                self.logger.debug(
                    "Failed to update wire_res_ohm from resistances", exc_info=True
                )
        self._write_legacy_settings_csv(out_dir / f"{prefix}_log.csv")
        self._save_settings_json(out_dir / f"{prefix}_run.json")
        self.logger.info(f"Saved spectra/log/plot to {out_dir}")

    def _save_plot(self, path: Path) -> None:
        """Write the current Matplotlib stack figure to *path*."""
        try:
            plt.figure("LPG spectra")
            plt.savefig(path, dpi=130, bbox_inches="tight")
        except Exception:
            self.logger.debug(f"Could not save plot to {path}", exc_info=True)

    def _write_legacy_settings_csv(self, path: Path) -> None:
        """Emit a CSV log compatible with the earlier tooling."""
        s = self.settings
        rows = [
            ("Directory", s.out_dir.resolve()),
            ("Filename", s.file_prefix),
            ('First series of inscriptions "Yes" or "No"', s.first_series),
            ("Curent in A", f"{s.target_current_a:.6f}"),
            ("time for heating in seconds", s.heat_time_s),
            ("number of period to write", s.n_periods),
            ("period in um", s.period_um),
            ("pause before taking OSA scan in seconds", s.sleep_before_scan_s),
            (
                "np.maximum dip in dB of OSA scan before terminating process",
                s.dip_limit_db,
            ),
            ("Time in seconds after turn on to measure resistance", s.measure_delay_s),
            ("Average resistance at previous writing", s.wire_res_ohm),
            ("'A' 'B' or 'C' OSA trace to read", s.osa_trace),
            ("OSA span in wl", s.osa_span_nm),
            ("Wavelength resolution in nm", s.osa_resolution_nm),
            ("Tension in g", s.tension_g),
            ("Comment", s.comment),
            ("Power supply type", s.psu_type),
            ("Sensitivity", s.osa_sensitivity),
        ]
        with path.open("w", encoding="utf-8") as fh:
            for key, value in rows:
                fh.write(f"{key},{value}\n")

    def _save_settings_json(self, path: Path) -> None:
        """Persist run settings to JSON for later reuse."""
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(self.settings.to_dict(), fh, indent=2)
        except Exception:
            self.logger.debug(f"Could not write settings JSON to {path}", exc_info=True)

    def _load_previous_run(self) -> FloatArray | None:
        """Return the saved spectra matrix if present on disk."""
        path = self.settings.out_dir / f"{self.settings.file_prefix}_spectra.csv"
        try:
            return np.loadtxt(path, delimiter=",")
        except Exception:
            return None

    def _safe_psu_off(self) -> None:
        """Best-effort PSU shutdown that tolerates transport errors."""
        try:
            self.psu.output = False
        except Exception:
            pass
