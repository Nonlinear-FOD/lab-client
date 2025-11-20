from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import (
    CameraROI,
    CameraWindow,
    PyCapture2CameraSettings,
    build_roi_payload,
)


class PyCapture2Client(LabDeviceClient):
    """HTTP client for the PyCapture2 sidecar camera service."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        settings: PyCapture2CameraSettings | None = None,
        auto_connect: bool = True,
        camera_kind: str | None = None,
        max_signal: float | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            base_url: Main server URL.
            device_name: Device identifier from the server config.
            user: Optional user tag propagated via ``X-User``.
            debug: Whether to include ``X-Debug`` headers.
            settings: Optional :class:`PyCapture2CameraSettings` applied on connect.
            auto_connect: If ``True``, call :meth:`connect_camera` automatically.
            camera_kind: Optional override forwarded to the server proxy.
            **kwargs: Extra overrides forwarded to ``connect`` on the lab server.
        """
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._settings = settings
        self._camera_kind = camera_kind.lower() if camera_kind else None
        self._max_signal = (
            float(max_signal) if max_signal is not None else self._default_max_signal()
        )
        self._shape: tuple[int, int] | None = None
        self._initialize_device(kwargs)
        if auto_connect:
            self.connect_camera(settings=settings, **kwargs)

    def connect_camera(
        self,
        settings: PyCapture2CameraSettings | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Connect (or reconnect) the camera with explicit settings."""
        payload: dict[str, Any] = {}
        if self._camera_kind:
            payload["camera_kind"] = self._camera_kind
        if settings is not None:
            payload.update(settings.to_payload())
        for key, value in overrides.items():
            if value is None:
                continue
            payload[key] = value
        if not payload:
            response = self._call_sidecar_dict("connect_sidecar")
        else:
            response = self._call_sidecar_dict("connect_sidecar", **payload)
        self._maybe_update_shape(response)
        return response

    def start_capture(self) -> dict[str, Any]:
        """Begin streaming frames on the remote sidecar."""
        return self._call_sidecar_dict("start_capture")

    def stop_capture(self) -> dict[str, Any]:
        """Stop streaming frames on the remote sidecar."""
        return self._call_sidecar_dict("stop_capture")

    def grab_frame(
        self,
        averages: int = 1,
        dtype: np.dtype | None = None,
        window: CameraWindow | dict[str, int] | None = None,
        output_pixels: int | None = None,
    ) -> tuple[np.ndarray, bool]:
        """Capture a frame with optional averaging/cropping/binning + overflow flag."""
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
        frame_payload: Any
        overflow_flag: Any
        if isinstance(result, dict):
            if "frame" not in result:
                raise RuntimeError("Camera response missing frame data")
            frame_payload = result["frame"]
            overflow_flag = result.get("overflow", False)
        elif isinstance(result, (list, tuple)) and len(result) == 2:
            frame_payload, overflow_flag = result
        else:
            raise RuntimeError(
                f"Unexpected payload from grab_frame: {type(result)!r}"
            )
        array = np.asarray(frame_payload)
        if dtype is not None:
            array = array.astype(dtype, copy=False)
        overflow = bool(overflow_flag)
        return array, overflow

    def configure_roi(
        self,
        roi: CameraROI | Mapping[str, Any] | None = None,
        **overrides: Any,
    ) -> dict[str, int]:
        """Update the Format7 ROI (width/height/offsets) at runtime."""
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

    def disconnect_camera(self) -> dict[str, Any]:
        """Disconnect the camera sidecar."""
        result = self._call_sidecar_dict("disconnect_sidecar")
        self._shape = None
        return result

    @property
    def max_signal(self) -> float:
        """Return the maximum digital count supported by this camera."""
        return self._max_signal

    def _default_max_signal(self) -> float:
        if self._camera_kind == "spiricon":
            return 65535.0
        return 255.0

    @property
    def camera_kind(self) -> str | None:
        """Return the configured camera kind override, if any."""
        return self._camera_kind

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

    def _call_sidecar_dict(self, method: str, **kwargs: Any) -> dict[str, Any]:
        """Invoke a sidecar method and ensure a mapping is returned."""
        result = self.call(method, **kwargs)
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Sidecar method '{method}' returned unexpected payload {type(result)!r}"
            )
        return dict(result)

    def _refresh_shape_from_status(self) -> None:
        """Query the server status endpoint to recover the hardware shape."""
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
