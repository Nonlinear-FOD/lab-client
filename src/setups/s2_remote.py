"""Prototype scaffolding for remote S2 measurements.

This module wires together the existing device clients (laser, camera, etc.)
so you can orchestrate a full S2 sequence across multiple lab servers. It keeps
the logic deliberately thin for now—just enough to connect, grab a frame, and
plug in laser steps—so you can iterate quickly before porting the GUI.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol

import numpy as np
import numpy.typing as npt

from clients.camera_models import BobcatCameraSettings, PyCapture2CameraSettings
from clients.chameleon_client import ChameleonClient
from clients.laser_clients import (
    AgilentLaserClient,
    AndoLaserClient,
    TiSapphireClient,
)
from clients.bobcat_client import BobcatClient
from clients.spiricon_client import SpiriconClient
from clients.thorlabs_camera_client import ThorlabsCameraClient


@dataclass
class DeviceEndpoint:
    """Minimal info needed to instantiate a remote device client."""

    base_url: str
    device_name: str
    user: str | None = None
    init_kwargs: dict[str, Any] = field(default_factory=dict)


class CameraProtocol(Protocol):
    """Minimal surface expected from camera clients used in S2RemoteSetup."""

    def grab_frame(self, *args: Any, **kwargs: Any) -> np.ndarray: ...
    def close(self) -> None: ...
    @property
    def max_signal(self) -> int | float: ...


class LaserProtocol(Protocol):
    @property
    def wavelength(self) -> float: ...

    @wavelength.setter
    def wavelength(self, value: float) -> None: ...

    def enable(self) -> None: ...
    def disable(self) -> None: ...
    def close(self) -> None: ...


@dataclass
class S2ScanConfig:
    """Parameters describing a wavelength sweep."""

    start_nm: float
    stop_nm: float
    step_nm: float
    settle_s: float = 0.2
    averages: int = 1  # grab N frames per wavelength and average

    def wavelengths(self) -> Iterable[float]:
        if self.step_nm == 0:
            raise ValueError("step_nm must be non-zero")
        count = int(round((self.stop_nm - self.start_nm) / self.step_nm)) + 1
        for idx in range(max(1, count)):
            yield self.start_nm + idx * self.step_nm


@dataclass
class S2ImageWindow:
    """Pixel region (x/y) to cut from the raw camera frame."""

    x_start: int
    x_end: int
    y_start: int
    y_end: int

    def as_slices(self, frame_shape: tuple[int, int]) -> tuple[slice, slice]:
        height, width = frame_shape
        x0 = max(0, min(self.x_start, width - 1))
        x1 = max(x0 + 1, min(self.x_end, width))
        y0 = max(0, min(self.y_start, height - 1))
        y1 = max(y0 + 1, min(self.y_end, height))
        return slice(y0, y1), slice(x0, x1)

    def to_payload(self) -> dict[str, int]:
        return {
            "x_start": int(self.x_start),
            "x_end": int(self.x_end),
            "y_start": int(self.y_start),
            "y_end": int(self.y_end),
        }


@dataclass
class S2ProcessingConfig:
    """Image processing and averaging parameters for an S2 scan."""

    window: S2ImageWindow
    output_pixels: int = 64
    background_frames: int = 1
    transform: str = "linear"  # or "scintacor"
    dtype: npt.DTypeLike | str | None = np.floating
    server_binning: bool = False

    def normalized_dtype(self) -> npt.DTypeLike | None:
        if self.dtype is None:
            return None
        return np.dtype(self.dtype)


@dataclass
class S2ScanResult:
    """Processed scan cube plus metadata."""

    wavelengths_nm: np.ndarray
    cube: np.ndarray  # shape: (steps, rows, cols)
    metadata: dict[str, Any]
    raw_frames: list[np.ndarray] | None = None

    def save_npz(self, path: str | Path) -> Path:
        out_path = Path(path)
        np.savez(
            out_path,
            wavelengths=self.wavelengths_nm,
            cube=self.cube,
            metadata=np.array(self.metadata, dtype=object),
        )
        return out_path

    def to_legacy_array(self) -> np.ndarray:
        """Return data in the legacy GUI format (wavelength + flattened image)."""
        steps = self.cube.shape[0]
        frames = self.cube.reshape(steps, -1)
        return np.column_stack((self.wavelengths_nm.reshape(-1, 1), frames))

    def save_legacy_npy(self, path: str | Path) -> Path:
        """Persist the legacy .npy layout used by GUI_take_S2."""
        out_path = Path(path)
        np.save(out_path, self.to_legacy_array())
        return out_path


@dataclass
class S2RemoteSetup:
    """Composable orchestrator for S2 experiments using remote instruments."""

    camera: DeviceEndpoint
    laser: DeviceEndpoint
    camera_kind: str = "chameleon"  # or "spiricon", "thorlabs", "bobcat"
    laser_kind: str = "ando"  # or "agilent", "tisa"
    _cam_client: CameraProtocol | None = field(init=False, default=None)
    _laser_client: LaserProtocol | None = field(init=False, default=None)
    _camera_max_signal: float | None = field(init=False, default=None)

    # ------------------------------------------------------------------ connect/disconnect
    def connect(self) -> None:
        """Instantiate all configured clients."""
        self._cam_client = self._connect_camera(self.camera_kind)
        self._laser_client = self._connect_laser(self.laser_kind)
        self._enable_laser_output()
        self._camera_max_signal = self._read_camera_max_signal()

    def disconnect(self) -> None:
        """Close all live clients."""
        for client in (self._cam_client, self._laser_client):
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
        self._camera_max_signal = None

    # ------------------------------------------------------------------ camera helpers
    def _connect_camera(self, kind: str) -> CameraProtocol:
        if kind == "chameleon":
            cam_kwargs = dict(self.camera.init_kwargs)
            settings = cam_kwargs.pop("settings", None)
            settings_obj = self._as_pycapture2_settings(settings)
            cam = ChameleonClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                settings=settings_obj,
                **cam_kwargs,
            )
            cam.start_capture()
            return cam
        if kind == "spiricon":
            cam_kwargs = dict(self.camera.init_kwargs)
            settings = cam_kwargs.pop("settings", None)
            settings_obj = self._as_pycapture2_settings(settings)
            cam = SpiriconClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                settings=settings_obj,
                **cam_kwargs,
            )
            cam.start_capture()
            return cam
        if kind == "bobcat":
            cam_kwargs = dict(self.camera.init_kwargs)
            settings = cam_kwargs.pop("settings", None)
            settings_obj = self._as_bobcat_settings(settings)
            cam = BobcatClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                settings=settings_obj,
                **cam_kwargs,
            )
            cam.start_capture()
            return cam
        if kind == "thorlabs":
            return ThorlabsCameraClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
        raise ValueError(f"Unsupported camera kind '{kind}'")

    @staticmethod
    def _as_pycapture2_settings(
        payload: PyCapture2CameraSettings | dict[str, Any] | None,
    ) -> PyCapture2CameraSettings | None:
        if payload is None:
            return None
        if isinstance(payload, PyCapture2CameraSettings):
            return payload
        if isinstance(payload, dict):
            return PyCapture2CameraSettings(**payload)
        raise TypeError("Unsupported settings payload for PyCapture2 camera")

    @staticmethod
    def _as_bobcat_settings(
        payload: BobcatCameraSettings | dict[str, Any] | None,
    ) -> BobcatCameraSettings | None:
        if payload is None:
            return None
        if isinstance(payload, BobcatCameraSettings):
            return payload
        if isinstance(payload, dict):
            return BobcatCameraSettings(**payload)
        raise TypeError("Unsupported settings payload for Bobcat camera")

    def grab_frame(self, averages: int = 1, **kwargs: Any) -> np.ndarray:
        """Fetch a frame from whichever camera is connected."""
        if self._cam_client is None:
            raise RuntimeError("Camera client not connected")
        return self._cam_client.grab_frame(averages=averages, **kwargs)

    # ------------------------------------------------------------------ laser helpers
    def _connect_laser(self, kind: str) -> LaserProtocol:
        factories = {
            "ando": AndoLaserClient,
            "agilent": AgilentLaserClient,
            "tisa": TiSapphireClient,
        }
        factory = factories.get(kind.lower())
        if factory is None:
            raise ValueError(f"Unsupported laser kind '{kind}'")
        return factory(
            self.laser.base_url,
            self.laser.device_name,
            user=self.laser.user,
            **self.laser.init_kwargs,
        )

    def _enable_laser_output(self) -> None:
        if self._laser_client is not None and hasattr(self._laser_client, "enable"):
            try:
                self._laser_client.enable()  # type: ignore[attr-defined]
                time.sleep(3)
            except Exception:
                pass

    def _set_laser_wavelength(self, wavelength_nm: float) -> None:
        laser = self._laser_client
        if laser is None:
            raise RuntimeError("Laser client not connected")
        if hasattr(laser, "wavelength"):
            setattr(laser, "wavelength", wavelength_nm)
            return
        if hasattr(laser, "set_wavelength"):
            ### Make sure that TiSa is calibrated when using this
            laser.set_wavelength(wavelength_nm)  # type: ignore[attr-defined]
            return
        raise RuntimeError("Connected laser does not expose wavelength control")

    # ------------------------------------------------------------------ measurement skeleton
    def run_single_step(
        self,
        wavelength_nm: float,
        averages: int = 1,
        settle_s: float = 0.0,
        frame_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Move laser, optionally wait, capture averaged frame, and return payload."""
        self._set_laser_wavelength(wavelength_nm)
        if settle_s > 0:
            time.sleep(settle_s)
        kwargs = frame_kwargs or {}
        frame = self.grab_frame(averages=averages, **kwargs)
        self._check_saturation(frame, context=f"{wavelength_nm:.3f} nm")
        return {
            "wavelength_nm": wavelength_nm,
            "frame": frame,
        }

    def run_scan(
        self,
        config: S2ScanConfig,
        *,
        frame_kwargs: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute an S2 sweep over the configured wavelength span."""
        results: list[dict[str, Any]] = []
        for wl in config.wavelengths():
            result = self.run_single_step(
                wl,
                averages=config.averages,
                settle_s=config.settle_s,
                frame_kwargs=frame_kwargs,
            )
            results.append(result)
        return results

    def _camera_frame_kwargs(
        self,
        processing: S2ProcessingConfig | None,
    ) -> dict[str, Any]:
        if processing is None or not processing.server_binning:
            return {}
        roi = processing.window.to_payload()
        output = max(1, int(processing.output_pixels))
        return {"window": roi, "output_pixels": output}

    # ------------------------------------------------------------------ higher-level workflow
    def capture_background(
        self,
        *,
        averages: int,
        frames: int,
        frame_kwargs: dict[str, Any] | None = None,
    ) -> np.ndarray:
        """Average several frames to form a background image."""
        samples = max(1, int(frames))
        captures: list[np.ndarray] = []
        kwargs = frame_kwargs or {}
        for _ in range(samples):
            frame = self.grab_frame(averages=averages, **kwargs)
            self._check_saturation(frame, context="background")
            captures.append(frame)
        if len(captures) == 1:
            return captures[0]
        return np.mean(captures, axis=0)

    def run_processed_scan(
        self,
        scan: S2ScanConfig,
        processing: S2ProcessingConfig,
        *,
        save_path: str | Path | None = None,
    ) -> S2ScanResult:
        """Capture a full scan and return the processed (cropped/binned) cube."""
        wavelengths = list(scan.wavelengths())
        if not wavelengths:
            raise ValueError("Scan produced no wavelengths—check step size")

        camera_averages = max(1, int(scan.averages))
        frame_kwargs = self._camera_frame_kwargs(processing)
        background = self.capture_background(
            averages=camera_averages,
            frames=processing.background_frames,
            frame_kwargs=frame_kwargs,
        )
        processed_frames: list[np.ndarray] = []
        raw_frames: list[np.ndarray] = []
        for wavelength in wavelengths:
            step = self.run_single_step(
                wavelength,
                averages=camera_averages,
                settle_s=scan.settle_s,
                frame_kwargs=frame_kwargs,
            )
            raw = np.asarray(step["frame"], dtype=float)
            raw_frames.append(raw)
            processed_frames.append(
                self._process_frame(raw, background, processing),
            )

        cube = np.stack(processed_frames, axis=0)
        metadata = {
            "scan": asdict(scan),
            "processing": asdict(processing),
            "camera_kind": self.camera_kind,
            "laser_kind": self.laser_kind,
        }
        result = S2ScanResult(
            wavelengths_nm=np.asarray(wavelengths, dtype=float),
            cube=cube,
            metadata=metadata,
            raw_frames=raw_frames,
        )
        if save_path is not None:
            result.save_npz(save_path)
        return result

    # ------------------------------------------------------------------ internal helpers
    def _process_frame(
        self,
        frame: np.ndarray,
        background: np.ndarray,
        processing: S2ProcessingConfig,
    ) -> np.ndarray:
        working = frame.astype(np.float64, copy=False)
        working -= background
        working = self._apply_transform(working, processing.transform)
        region = working
        if not processing.server_binning:
            region = self._crop_frame(region, processing.window)
        if not processing.server_binning:
            region = self._bin_frame(region, processing.output_pixels)
        dtype = processing.normalized_dtype()
        if dtype is not None:
            return region.astype(dtype, copy=False)
        return region

    def _read_camera_max_signal(self) -> float | None:
        client = self._cam_client
        if client is None:
            return None
        value = getattr(client, "max_signal", None)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _check_saturation(self, frame: np.ndarray, context: str) -> None:
        if self._camera_max_signal is None:
            return
        max_val = float(np.nanmax(frame))
        if max_val >= 0.98 * self._camera_max_signal:
            print(
                f"[S2] Warning: frame near saturation ({max_val:.1f} / "
                f"{self._camera_max_signal:.1f}) during {context}",
            )

    @staticmethod
    def _apply_transform(frame: np.ndarray, transform: str) -> np.ndarray:
        if transform.lower() == "scintacor":
            return np.sign(frame) * np.sqrt(np.abs(frame))
        return frame

    @staticmethod
    def _crop_frame(frame: np.ndarray, window: S2ImageWindow) -> np.ndarray:
        y_slice, x_slice = window.as_slices(frame.shape)
        return frame[y_slice, x_slice]

    @staticmethod
    def _bin_frame(region: np.ndarray, target_pixels: int) -> np.ndarray:
        if target_pixels <= 0:
            raise ValueError("output_pixels must be positive")
        height, width = region.shape
        if height < 2 or width < 2:
            raise ValueError("ROI is too small to bin")
        span = min(height, width)
        bin_size = max(1, round(span / target_pixels))
        rows = height // bin_size
        cols = width // bin_size
        trimmed = region[: rows * bin_size, : cols * bin_size]
        if trimmed.size == 0:
            raise ValueError("Binning trimmed the entire frame—adjust ROI or pixels")
        reshaped = trimmed.reshape(rows, bin_size, cols, bin_size)
        return reshaped.mean(axis=(1, 3))
