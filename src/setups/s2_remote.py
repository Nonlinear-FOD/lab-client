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
from typing import Any, Dict, Iterable, List, Protocol

import numpy as np

from clients.chameleon_client import ChameleonClient
from clients.laser_clients import (
    AgilentLaserClient,
    AndoLaserClient,
    TiSapphireClient,
)
from clients.thorlabs_camera_client import ThorlabsCameraClient


@dataclass
class DeviceEndpoint:
    """Minimal info needed to instantiate a remote device client."""

    base_url: str
    device_name: str
    user: str | None = None
    init_kwargs: Dict[str, Any] = field(default_factory=dict)


class CameraProtocol(Protocol):
    def grab_frame(self, averages: int = 1) -> np.ndarray: ...
    def close(self) -> None: ...


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


@dataclass
class S2ProcessingConfig:
    """Image processing and averaging parameters for an S2 scan."""

    window: S2ImageWindow
    output_pixels: int = 64
    background_frames: int = 1
    transform: str = "linear"  # or "scintacor"
    dtype: np.dtype | str | None = np.float32

    def normalized_dtype(self) -> np.dtype | None:
        if self.dtype is None:
            return None
        return np.dtype(self.dtype)


@dataclass
class S2ScanResult:
    """Processed scan cube plus metadata."""

    wavelengths_nm: np.ndarray
    cube: np.ndarray  # shape: (steps, rows, cols)
    metadata: Dict[str, Any]
    raw_frames: List[np.ndarray] | None = None

    def save_npz(self, path: str | Path) -> Path:
        out_path = Path(path)
        np.savez(
            out_path,
            wavelengths=self.wavelengths_nm,
            cube=self.cube,
            metadata=self.metadata,
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
    camera_kind: str = "chameleon"  # or "thorlabs"
    laser_kind: str = "ando"  # or "agilent", "tisa"
    _cam_client: CameraProtocol | None = field(init=False, default=None)
    _laser_client: LaserProtocol | None = field(init=False, default=None)

    # ------------------------------------------------------------------ connect/disconnect
    def connect(self) -> None:
        """Instantiate all configured clients."""
        self._cam_client = self._connect_camera(self.camera_kind)
        self._laser_client = self._connect_laser(self.laser_kind)
        self._enable_laser_output()

    def disconnect(self) -> None:
        """Close all live clients."""
        for client in (self._cam_client, self._laser_client):
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ camera helpers
    def _connect_camera(self, kind: str) -> CameraProtocol:
        if kind == "chameleon":
            cam = ChameleonClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
            cam.connect_camera()
            cam.start_capture()
            time.sleep(2)
            return cam
        if kind == "thorlabs":
            return ThorlabsCameraClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
        raise ValueError(f"Unsupported camera kind '{kind}'")

    def grab_frame(self, averages: int = 1) -> np.ndarray:
        """Fetch a frame from whichever camera is connected."""
        if self._cam_client is None:
            raise RuntimeError("Camera client not connected")
        return self._cam_client.grab_frame(averages=averages)

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
    ) -> Dict[str, Any]:
        """Move laser, optionally wait, capture averaged frame, and return payload."""
        self._set_laser_wavelength(wavelength_nm)
        if settle_s > 0:
            time.sleep(settle_s)
        frame = self.grab_frame(averages=averages)
        return {
            "wavelength_nm": wavelength_nm,
            "frame": frame,
        }

    def run_scan(self, config: S2ScanConfig) -> List[Dict[str, Any]]:
        """Execute an S2 sweep over the configured wavelength span."""
        results: List[Dict[str, Any]] = []
        for wl in config.wavelengths():
            result = self.run_single_step(
                wl,
                averages=config.averages,
                settle_s=config.settle_s,
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------ higher-level workflow
    def capture_background(
        self,
        *,
        averages: int,
        frames: int,
    ) -> np.ndarray:
        """Average several frames to form a background image."""
        samples = max(1, int(frames))
        captures: List[np.ndarray] = []
        for _ in range(samples):
            captures.append(self.grab_frame(averages=averages))
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
        background = self.capture_background(
            averages=camera_averages,
            frames=processing.background_frames,
        )
        processed_frames: List[np.ndarray] = []
        raw_frames: List[np.ndarray] = []
        for wavelength in wavelengths:
            step = self.run_single_step(
                wavelength,
                averages=camera_averages,
                settle_s=scan.settle_s,
            )
            raw = np.asarray(step["frame"])
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
        cropped = self._crop_frame(working, processing.window)
        binned = self._bin_frame(cropped, processing.output_pixels)
        dtype = processing.normalized_dtype()
        if dtype is not None:
            return binned.astype(dtype, copy=False)
        return binned

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
