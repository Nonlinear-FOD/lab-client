from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import (
    BobcatCameraSettings,
    CameraROI,
    CameraWindow,
    build_roi_payload,
)


class BobcatClient(LabDeviceClient):
    """HTTP client for the Bobcat CVB camera sidecar."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        settings: BobcatCameraSettings | None = None,
        auto_connect: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._settings = settings
        self._shape: tuple[int, int] | None = None
        self._initialize_device(kwargs)
        if auto_connect:
            self.connect_camera(settings=settings)

    def connect_camera(
        self,
        settings: BobcatCameraSettings | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Connect (or reconnect) the camera with explicit settings."""
        payload: dict[str, Any] = {}
        if settings is not None:
            payload.update(settings.to_payload())
        for key, value in overrides.items():
            if value is None:
                continue
            payload[key] = value
        if not payload:
            response = dict(self.call("connect_sidecar"))
        else:
            response = dict(self.call("connect_sidecar", **payload))
        self._maybe_update_shape(response)
        return response

    def start_capture(self) -> dict[str, Any]:
        """Begin streaming frames on the remote sidecar."""
        return dict(self.call("start_capture"))

    def stop_capture(self) -> dict[str, Any]:
        """Stop streaming frames on the remote sidecar."""
        return dict(self.call("stop_capture"))

    def grab_frame(
        self,
        averages: int = 1,
        dtype: np.dtype | None = None,
        window: CameraWindow | dict[str, int] | None = None,
        output_pixels: int | None = None,
    ) -> tuple[np.ndarray, bool]:
        """Capture a frame with optional averaging/cropping/binning plus overflow flag."""
        payload: dict[str, Any] = {}
        if averages and int(averages) > 1:
            payload["averages"] = int(averages)
        if window:
            if isinstance(window, CameraWindow):
                payload["window"] = window.to_payload()
            else:
                payload["window"] = {k: int(v) for k, v in window.items()}
        if output_pixels is not None:
            payload["output_pixels"] = int(output_pixels)
        result = self.call("grab_frame", **payload)
        if not isinstance(result, dict) or "frame" not in result:
            raise RuntimeError("Camera response missing frame data")
        array = np.asarray(result["frame"])
        if dtype is not None:
            array = array.astype(dtype, copy=False)
        overflow = bool(result.get("overflow", False))
        return array, overflow

    def disconnect_camera(self) -> dict[str, Any]:
        """Disconnect the camera sidecar."""
        result = dict(self.call("disconnect_sidecar"))
        self._shape = None
        return result

    @property
    def max_signal(self) -> float:
        """Return the maximum digital count supported by this camera."""
        return 35300.0

    def configure_roi(
        self,
        roi: CameraROI | Mapping[str, Any] | None = None,
        **overrides: Any,
    ) -> dict[str, int]:
        payload = build_roi_payload(roi, overrides)
        if not payload:
            raise ValueError("configure_roi requires at least one ROI parameter")
        result = self.call("configure_roi", **payload)
        if not isinstance(result, dict):
            raise RuntimeError("Sidecar did not return ROI payload")
        applied = {
            "offset_x": int(result["offset_x"]),
            "offset_y": int(result["offset_y"]),
            "width": int(result["width"]),
            "height": int(result["height"]),
        }
        self._shape = (applied["height"], applied["width"])
        return applied

    @property
    def shape(self) -> tuple[int, int]:
        """Return the current hardware frame shape (height, width)."""
        if self._shape is None:
            self._refresh_shape_from_status()
        if self._shape is None:
            raise RuntimeError("Camera has not reported a native frame shape")
        return self._shape

    def close(self) -> None:
        """Disconnect the camera and underlying HTTP session."""
        try:
            self.disconnect_camera()
        finally:
            self.disconnect()

    def _refresh_shape_from_status(self) -> None:
        try:
            status = self.call("status")
        except Exception:
            return
        if isinstance(status, dict):
            self._maybe_update_shape(status)

    def _maybe_update_shape(self, payload: Mapping[str, Any]) -> None:
        shape = payload.get("shape")
        if isinstance(shape, (list, tuple)) and len(shape) == 2:
            try:
                height = int(shape[0])
                width = int(shape[1])
            except Exception:
                pass
            else:
                self._shape = (height, width)
                return
        if isinstance(shape, dict):
            height = shape.get("height")
            width = shape.get("width")
            if height is not None and width is not None:
                self._shape = (int(height), int(width))
