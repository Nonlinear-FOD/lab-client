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

from clients.camera_models import (
    BobcatCameraSettings,
    PyCapture2CameraSettings,
)
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

    def grab_frame(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, bool]: ...

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


def center_of_mass(frame: np.ndarray) -> tuple[int, int]:
    f = np.asarray(frame, dtype=float)
    total = f.sum()
    y = np.arange(f.shape[0])
    x = np.arange(f.shape[1])
    cy = np.dot(f.sum(axis=1), y) / total
    cx = np.dot(f.sum(axis=0), x) / total
    cx_i = int(np.rint(cx))
    cy_i = int(np.rint(cy))
    return cx_i, cy_i


@dataclass(slots=True)
class S2ImageWindow:
    """Rectangular ROI expressed via offset + size."""

    offset_x: int
    offset_y: int
    width: int
    height: int

    @classmethod
    def from_center(
        cls,
        center: tuple[int, int],
        width: int,
        height: int,
        add_offset_x: int = 0,
        add_offset_y: int = 0,
    ) -> "S2ImageWindow":
        cx = center[0] + add_offset_x
        cy = center[1] + add_offset_y
        half_w = width // 2
        half_h = height // 2
        return cls(cx - half_w, cy - half_h, width, height)

    def recentered(self, center: tuple[int, int]) -> "S2ImageWindow":
        return type(self).from_center(
            center, self.width, self.height, self.offset_x, self.offset_y
        )

    @property
    def x_end(self) -> int:
        return int(self.offset_x + self.width)

    @property
    def y_end(self) -> int:
        return int(self.offset_y + self.height)

    def clamp(self, frame_shape: tuple[int, int]) -> "S2ImageWindow":
        height, width = frame_shape
        offset_x = max(0, min(int(self.offset_x), width - 1))
        offset_y = max(0, min(int(self.offset_y), height - 1))
        width_val = max(1, int(self.width))
        height_val = max(1, int(self.height))
        width_val = min(width_val, max(1, width - offset_x))
        height_val = min(height_val, max(1, height - offset_y))
        return S2ImageWindow(offset_x, offset_y, width_val, height_val)

    def as_slices(self, frame_shape: tuple[int, int]) -> tuple[slice, slice]:
        clamped = self.clamp(frame_shape)
        x0 = clamped.offset_x
        x1 = clamped.offset_x + clamped.width
        y0 = clamped.offset_y
        y1 = clamped.offset_y + clamped.height
        return slice(y0, y1), slice(x0, x1)

    def to_crop_payload(self) -> dict[str, int]:
        x0 = int(self.offset_x)
        y0 = int(self.offset_y)
        return {
            "x_start": x0,
            "x_end": x0 + int(self.width),
            "y_start": y0,
            "y_end": y0 + int(self.height),
        }

    def scaled(self, scale_x: float, scale_y: float | None = None) -> "S2ImageWindow":
        scale_y = scale_y if scale_y is not None else scale_x
        return S2ImageWindow(
            offset_x=int(round(self.offset_x * scale_x)),
            offset_y=int(round(self.offset_y * scale_y)),
            width=max(1, int(round(self.width * scale_x))),
            height=max(1, int(round(self.height * scale_y))),
        )


@dataclass
class S2ProcessingConfig:
    """Image processing and averaging parameters for an S2 scan."""

    window: S2ImageWindow
    output_pixels: int = 64
    background_frames: int = 1
    transform: str = "linear"


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

    def __init__(
        self,
        cmap: str = "magma",
        max_fps_samples: int = 25,
        overlay_window: S2ImageWindow | None = None,
    ):
        self.cmap = cmap
        self.max_fps_samples = max(2, int(max_fps_samples))
        self._timestamps: deque[float] = deque(maxlen=self.max_fps_samples)
        self._frame_count = 0
        self._plt = None
        self.fig = None
        self.ax = None
        self._image = None
        self._overlay_window = overlay_window
        self._overlay_patch = None
        self._centroid_marker = None

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
        self._update_overlay(frame)

    def update(
        self,
        frame: np.ndarray,
        *,
        status: str = "",
        overflow: bool = False,
        grab_latency_ms: float | None = None,
        centroid: tuple[int, int] | None = None,
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
        self._update_overlay(frame, centroid=centroid)

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

    def _update_overlay(
        self, frame: np.ndarray, centroid: tuple[int, int] | None = None
    ) -> None:
        if self._overlay_window is None or self.ax is None:
            return
        window = self._overlay_window.clamp(frame.shape)
        try:
            import matplotlib.patches as patches
        except Exception:
            return
        if self._overlay_patch is None:
            rect = patches.Rectangle(
                (window.offset_x, window.offset_y),
                window.width,
                window.height,
                linewidth=1.5,
                edgecolor="cyan",
                facecolor="none",
            )
            self.ax.add_patch(rect)
            self._overlay_patch = rect
        else:
            self._overlay_patch.set_xy((window.offset_x, window.offset_y))
            self._overlay_patch.set_width(window.width)
            self._overlay_patch.set_height(window.height)
        if centroid is not None:
            if self._centroid_marker is None:
                (self._centroid_marker,) = self.ax.plot(
                    centroid[0],
                    centroid[1],
                    marker="x",
                    markersize=8,
                    mew=2,
                    color="lime",
                )
            else:
                self._centroid_marker.set_data([centroid[0]], [centroid[1]])

    def close(self) -> None:
        if self._plt is not None and self.fig is not None and self.is_open():
            self._plt.close(self.fig)
        self.fig = None
        self.ax = None
        self._image = None
        self._plt = None
        self._timestamps.clear()
        self._frame_count = 0
        self._overlay_patch = None


@dataclass
class S2RemoteSetup:
    """Orchestrator for S2 experiments using remote instruments."""

    camera: DeviceEndpoint
    laser: DeviceEndpoint
    laser_kind: str = "ando"  # or "agilent", "tisa"
    _cam_client: CameraProtocol | None = field(init=False, default=None)
    _laser_client: LaserProtocol | None = field(init=False, default=None)
    _connected: bool = False

    def __post_init__(self):
        self.camera_kind = _get_camera_kind(self.camera.device_name)
        self._active_hardware_shape: tuple[int, int] | None = None
        self._laser_output_enabled = False
        self._laser_warmup_s = 5.0

    # ------------------------------------------------------------------ connect/disconnect
    def connect(self) -> None:
        """Instantiate all configured clients."""
        if self._cam_client is None:
            self._cam_client = self._connect_camera(self.camera_kind)
        if self._laser_client is None:
            self._laser_client = self._connect_laser(self.laser_kind)
        if not self._laser_output_enabled:
            self._enable_laser_output()
        self._refresh_hardware_shape()
        self._connected = (
            self._cam_client is not None and self._laser_client is not None
        )

    def disconnect(self) -> None:
        """Close all live clients."""
        for client in (self._cam_client, self._laser_client):
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
        self._cam_client = None
        self._laser_client = None
        self._active_hardware_shape = None
        self._laser_output_enabled = False
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

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
            self._flush_camera(cam)
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
            self._flush_camera(cam)
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
            self._flush_camera(cam)
            return cam
        if kind == "thorlabs":
            cam = ThorlabsCameraClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
            self._flush_camera(cam)
            return cam
        raise ValueError(f"Unsupported camera kind '{kind}'")

    def _flush_camera(self, client: CameraProtocol, frames: int = 5) -> None:
        """Discard a few frames so sensors/sidecars can settle."""
        try:
            for _ in range(max(0, int(frames))):
                client.grab_frame()
        except Exception:
            pass

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
        frame, overflow = self._cam_client.grab_frame(averages=averages, **kwargs)
        return np.asarray(frame), overflow

    def _refresh_hardware_shape(self) -> None:
        client = self._cam_client
        if client is None:
            return
        try:
            shape = client.shape  # type: ignore[attr-defined]
        except Exception:
            return
        if isinstance(shape, (tuple, list)) and len(shape) == 2:
            try:
                height, width = int(shape[0]), int(shape[1])
            except Exception:
                return
            self._active_hardware_shape = (height, width)

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
                time.sleep(self._laser_warmup_s)
            except Exception:
                return
            self._laser_output_enabled = True

    def _disable_laser_output(self) -> None:
        if self._laser_client is not None and hasattr(self._laser_client, "disable"):
            try:
                self._laser_client.disable()  # type: ignore[attr-defined]
                time.sleep(1)
            except Exception:
                return
            self._laser_output_enabled = False

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
    ) -> S2ImageWindow | None:
        """Open a Matplotlib live view that streams frames until closed."""
        if not enable_preview:
            return
        if self._cam_client is None:
            raise RuntimeError("Camera client not connected")

        averages = max(1, int(frame_averages or 1))
        cam_kwargs = dict(frame_kwargs or {})
        if not cam_kwargs and processing is not None:
            cam_kwargs = {}
        if processing is not None:
            base_offset_x = processing.window.offset_x
            base_offset_y = processing.window.offset_y
            w = processing.window.width
            h = processing.window.height
            preview_overlay = processing.window
        else:
            preview_overlay = None
            base_offset_x = 0
            base_offset_y = 0
            w = 0
            h = 0

        preview = _LivePreviewWindow(
            cmap=cmap,
            max_fps_samples=max_fps_samples,
            overlay_window=preview_overlay,
        )
        frame_count = 0
        last_log = time.perf_counter()
        centroid = None

        try:
            while True:
                start = time.perf_counter()
                frame, overflow = self.grab_frame(averages=averages, **cam_kwargs)
                frame = np.asarray(frame)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                frame_count += 1
                if processing is not None:
                    centroid = center_of_mass(frame)
                    if frame_count == 1:
                        # Only update the rectangle for first frame, otherwise run again
                        win = S2ImageWindow.from_center(
                            centroid,
                            w,
                            h,
                            add_offset_x=base_offset_x,
                            add_offset_y=base_offset_y,
                        ).clamp(frame.shape)
                        processing.window = win
                        preview._overlay_window = win  # keep overlay in syncg

                if overflow:
                    self._warn_overflow(True, context="live preview")
                if not preview.update(
                    frame,
                    status="",
                    overflow=overflow,
                    grab_latency_ms=elapsed_ms,
                    centroid=centroid if centroid else None,
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
            return preview._overlay_window
        finally:
            preview.close()
            return preview._overlay_window

    def _camera_frame_kwargs(
        self,
        processing: S2ProcessingConfig | None,
        *,
        window: S2ImageWindow | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if window is not None:
            payload["window"] = window.to_crop_payload()
        if processing is not None:
            payload["output_pixels"] = max(1, int(processing.output_pixels))
        return payload

    def _server_window_for(
        self,
        processing: S2ProcessingConfig | None,
    ) -> S2ImageWindow | None:
        if processing is None:
            return None
        if self._active_hardware_shape is None:
            return processing.window
        return processing.window.clamp(self._active_hardware_shape)

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
        restore_laser = False
        if self._laser_output_enabled:
            self._disable_laser_output()
            restore_laser = True
        for _ in range(samples):
            frame, overflow = self.grab_frame(averages=averages, **kwargs)
            self._warn_overflow(overflow, context="background")
            captures.append(frame)
        if restore_laser:
            self._enable_laser_output()
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
        server_window = self._server_window_for(processing)
        frame_kwargs = self._camera_frame_kwargs(
            processing,
            window=server_window,
        )
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
        # Grab a full-frame image with no cropping so the camera view returns
        # to its original window after the scan.
        try:
            self.grab_frame()
        except Exception:
            pass
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
        return self._apply_transform(working, processing.transform)

    @staticmethod
    def _apply_transform(frame: np.ndarray, transform: str) -> np.ndarray:
        if transform.lower() == "scintacor":
            return np.sign(frame) * np.sqrt(np.abs(frame))
        return frame
