"""Prototype scaffolding for remote S2 measurements.

This module wires together the existing device clients (laser, camera, etc.)
so you can orchestrate a full S2 sequence across multiple lab servers. It keeps
the logic deliberately thin for now—just enough to connect, grab a frame, and
plug in laser steps—so you can iterate quickly before porting the GUI.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol

import numpy as np

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


def _get_camera_kind(camera_name: str) -> str:
    if camera_name == "chameleon_scintacor" or camera_name == "chameleon_1mu":
        return "chameleon"
    elif camera_name == "thorlabs_camera":
        return "thorlabs"
    elif camera_name == "bobcat_camera":
        return "bobcat"
    else:
        raise ValueError("Invalid camera name")


@dataclass
class DeviceEndpoint:
    """Minimal info needed to instantiate a remote device client."""

    base_url: str
    device_name: str
    user: str | None = None
    init_kwargs: dict[str, Any] = field(default_factory=dict)


class CameraProtocol(Protocol):
    """Minimal surface expected from camera clients used in S2RemoteSetup."""

    def grab_frame(
        self, *args: Any, **kwargs: Any
    ) -> tuple[np.ndarray, bool]: ...

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
    live_preview: bool = True

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
    transform: str = "linear"
    server_binning: bool = True


@dataclass
class S2ScanResult:
    """Processed scan cube plus metadata (including per-step overflow flags)."""

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


class _LivePreviewWindow:
    """Simple Matplotlib window that streams frames with status text."""

    def __init__(self, cmap: str = "magma", max_fps_samples: int = 25):
        self.cmap = cmap
        self.max_fps_samples = max(2, int(max_fps_samples))
        self._timestamps: deque[float] = deque(maxlen=self.max_fps_samples)
        self._frame_count = 0
        self._plt = None
        self.fig = None
        self.ax = None
        self._image = None

    def is_open(self) -> bool:
        if self._plt is None or self.fig is None:
            return False
        return self._plt.fignum_exists(self.fig.number)

    def _init_plot(self, frame: np.ndarray) -> None:
        import matplotlib.pyplot as plt

        self._plt = plt
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self._image = self.ax.imshow(frame, cmap=self.cmap)
        self.ax.set_title("Initializing…")
        self.fig.colorbar(self._image, ax=self.ax, fraction=0.046, pad=0.04)
        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
        self._timestamps.clear()
        self._frame_count = 0

    def update(
        self,
        frame: np.ndarray,
        *,
        status: str = "",
        overflow: bool = False,
        grab_latency_ms: float | None = None,
    ) -> bool:
        frame = np.asarray(frame)
        if frame.size == 0:
            return self.is_open()
        if not self.is_open():
            self._init_plot(frame)
        assert self._image is not None and self.ax is not None and self._plt is not None

        self._frame_count += 1
        self._image.set_data(frame)
        try:
            vmin = float(np.nanmin(frame))
        except ValueError:
            vmin = 0.0
        try:
            vmax = float(np.nanmax(frame))
        except ValueError:
            vmax = vmin + 1e-6
        if not np.isfinite(vmin):
            vmin = 0.0
        if not np.isfinite(vmax) or vmax <= vmin:
            vmax = vmin + 1e-6
        self._image.set_clim(vmin=vmin, vmax=vmax)

        now = time.perf_counter()
        self._timestamps.append(now)
        if len(self._timestamps) > 1:
            elapsed = self._timestamps[-1] - self._timestamps[0]
            fps = (len(self._timestamps) - 1) / elapsed if elapsed > 0 else float("nan")
        else:
            fps = float("nan")

        parts = [f"{self._frame_count} frames"]
        if np.isfinite(fps):
            parts.append(f"{fps:.1f} FPS")
        if grab_latency_ms is not None:
            parts.append(f"{grab_latency_ms:.1f} ms")
        if status:
            parts.append(status)
        if overflow:
            parts.append("SATURATED")
        self.ax.set_title(" | ".join(parts))

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        self._plt.pause(0.001)
        return self.is_open()

    def close(self) -> None:
        if self._plt is not None and self.fig is not None and self.is_open():
            self._plt.close(self.fig)
        self.fig = None
        self.ax = None
        self._image = None
        self._plt = None
        self._timestamps.clear()
        self._frame_count = 0


@dataclass
class S2RemoteSetup:
    """Orchestrator for S2 experiments using remote instruments."""

    camera: DeviceEndpoint
    laser: DeviceEndpoint
    laser_kind: str = "ando"  # or "agilent", "tisa"
    _cam_client: CameraProtocol | None = field(init=False, default=None)
    _laser_client: LaserProtocol | None = field(init=False, default=None)

    def __post_init__(self):
        self.camera_kind = _get_camera_kind(self.camera.device_name)

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

    def grab_frame(self, averages: int = 1, **kwargs: Any) -> tuple[np.ndarray, bool]:
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
        frame, overflow = self.grab_frame(averages=averages, **kwargs)
        self._warn_overflow(overflow, context=f"{wavelength_nm:.3f} nm")
        return {
            "wavelength_nm": wavelength_nm,
            "frame": frame,
            "overflow": overflow,
        }

    def run_scan(
        self,
        config: S2ScanConfig,
        *,
        frame_kwargs: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute an S2 sweep over the configured wavelength span."""
        preview = _LivePreviewWindow() if config.live_preview else None
        results: list[dict[str, Any]] = []
        for wl in config.wavelengths():
            step_start = time.perf_counter()
            result = self.run_single_step(
                wl,
                averages=config.averages,
                settle_s=config.settle_s,
                frame_kwargs=frame_kwargs,
            )
            elapsed_ms = (time.perf_counter() - step_start) * 1000.0
            if preview is not None:
                still_open = preview.update(
                    np.asarray(result["frame"]),
                    status=f"{wl:.3f} nm",
                    overflow=bool(result.get("overflow", False)),
                    grab_latency_ms=elapsed_ms,
                )
                if not still_open:
                    preview.close()
                    preview = None
            results.append(result)
        if preview is not None:
            preview.close()
        return results

    def live_preview(
        self,
        *,
        enable_preview: bool = True,
        processing: S2ProcessingConfig | None = None,
        frame_kwargs: dict[str, Any] | None = None,
        frame_averages: int | None = None,
        max_fps_samples: int = 25,
        cmap: str = "magma",
    ) -> None:
        """Open a Matplotlib live view that streams frames until closed."""
        if not enable_preview:
            return
        if self._cam_client is None:
            raise RuntimeError("Camera client not connected")

        averages = max(1, int(frame_averages or 1))
        cam_kwargs = dict(frame_kwargs or {})
        if not cam_kwargs and processing is not None:
            cam_kwargs = self._camera_frame_kwargs(processing)

        preview = _LivePreviewWindow(cmap=cmap, max_fps_samples=max_fps_samples)
        frame_count = 0
        last_log = time.perf_counter()

        try:
            while True:
                start = time.perf_counter()
                frame, overflow = self.grab_frame(averages=averages, **cam_kwargs)
                frame = np.asarray(frame)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                frame_count += 1

                if overflow:
                    self._warn_overflow(True, context="live preview")
                if not preview.update(
                    frame,
                    status="",
                    overflow=overflow,
                    grab_latency_ms=elapsed_ms,
                ):
                    break

                now = time.perf_counter()
                if now - last_log >= 1.0:
                    print(
                        f"[live] frame {frame_count} | {elapsed_ms:.1f} ms per request",
                    )
                    last_log = now
        except KeyboardInterrupt:
            print("Stopping live preview.")
        finally:
            preview.close()

    def _camera_frame_kwargs(
        self,
        processing: S2ProcessingConfig | None,
    ) -> dict[str, Any]:
        if processing is None or not processing.server_binning:
            return {}
        roi = processing.window.to_payload()
        output = max(1, int(processing.output_pixels))
        return {"window": roi, "output_pixels": output}

    def _warn_overflow(self, overflow: bool, context: str) -> None:
        if overflow:
            print(f"[S2] Warning: camera reported sensor saturation during {context}")

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
            frame, overflow = self.grab_frame(averages=averages, **kwargs)
            self._warn_overflow(overflow, context="background")
            captures.append(frame)
        if len(captures) == 1:
            return captures[0]
        return np.mean(captures, axis=0)

    def run_processed_scan(
        self,
        scan: S2ScanConfig,
        processing: S2ProcessingConfig,
        save_path: str | Path | None = None,
    ) -> S2ScanResult:
        """Capture a full scan and return the processed (cropped/binned) cube."""
        if self.camera_kind == "chameleon":
            processing.transform = "scintacor"
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
        overflow_flags: list[bool] = []
        preview = _LivePreviewWindow() if scan.live_preview else None
        for wavelength in wavelengths:
            step_start = time.perf_counter()
            step = self.run_single_step(
                wavelength,
                averages=camera_averages,
                settle_s=scan.settle_s,
                frame_kwargs=frame_kwargs,
            )
            raw = np.asarray(step["frame"], dtype=float)
            raw_frames.append(raw)
            # track sensor saturation status per wavelength step
            overflow_flags.append(bool(step.get("overflow", False)))
            processed = self._process_frame(raw, background, processing)
            processed_frames.append(processed)
            if preview is not None:
                elapsed_ms = (time.perf_counter() - step_start) * 1000.0
                still_open = preview.update(
                    processed,
                    status=f"{wavelength:.3f} nm",
                    overflow=bool(step.get("overflow", False)),
                    grab_latency_ms=elapsed_ms,
                )
                if not still_open:
                    preview.close()
                    preview = None

        cube = np.stack(processed_frames, axis=0)
        if preview is not None:
            preview.close()
        metadata = {
            "scan": asdict(scan),
            "processing": asdict(processing),
            "camera_kind": self.camera_kind,
            "laser_kind": self.laser_kind,
            "overflow_flags": overflow_flags,
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
        return region

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
