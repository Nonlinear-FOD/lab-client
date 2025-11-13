from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import BobcatCameraSettings, CameraWindow


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
        self._initialize_device(kwargs)
        if auto_connect:
            self.connect_camera(settings=settings)

    def connect_camera(
        self,
        settings: BobcatCameraSettings | None = None,
        **overrides: Any,
    ) -> Dict[str, Any]:
        """Connect (or reconnect) the camera with explicit settings."""
        payload: Dict[str, Any] = {}
        if settings is not None:
            payload.update(settings.to_payload())
        for key, value in overrides.items():
            if value is None:
                continue
            payload[key] = value
        if not payload:
            return dict(self.call("connect_sidecar"))
        return dict(self.call("connect_sidecar", **payload))

    def start_capture(self) -> Dict[str, Any]:
        """Begin streaming frames on the remote sidecar."""
        return dict(self.call("start_capture"))

    def stop_capture(self) -> Dict[str, Any]:
        """Stop streaming frames on the remote sidecar."""
        return dict(self.call("stop_capture"))

    def grab_frame(
        self,
        averages: int = 1,
        dtype: np.dtype | None = None,
        window: CameraWindow | Dict[str, int] | None = None,
        output_pixels: int | None = None,
    ) -> Tuple[np.ndarray, bool]:
        """Capture a frame with optional averaging/cropping/binning plus overflow flag."""
        payload: Dict[str, Any] = {}
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

    def disconnect_camera(self) -> Dict[str, Any]:
        """Disconnect the camera sidecar."""
        return dict(self.call("disconnect_sidecar"))

    @property
    def max_signal(self) -> float:
        """Return the maximum digital count supported by this camera."""
        return 35300.0

    def close(self) -> None:
        """Disconnect the camera and underlying HTTP session."""
        try:
            self.disconnect_camera()
        finally:
            self.disconnect()
