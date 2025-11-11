from __future__ import annotations

from typing import Any, Dict

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import CameraWindow, ChameleonCameraSettings


class ChameleonClient(LabDeviceClient):
    """HTTP client for the Chameleon sidecar camera service."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        settings: ChameleonCameraSettings | None = None,
        auto_connect: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            base_url: Main server URL.
            device_name: Device identifier from the server config.
            user: Optional user tag propagated via ``X-User``.
            debug: Whether to include ``X-Debug`` headers.
            settings: Optional :class:`ChameleonCameraSettings` applied on connect.
            auto_connect: If ``True``, call :meth:`connect_camera` automatically.
            **kwargs: Extra overrides forwarded to ``connect`` on the lab server.
        """
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._settings = settings
        self._initialize_device(kwargs)
        if auto_connect:
            self.connect_camera(settings=settings)

    def connect_camera(
        self,
        settings: ChameleonCameraSettings | None = None,
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
    ) -> np.ndarray:
        """Capture a frame with optional averaging, windowing and binning."""
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
        frame = self.call("grab_frame", **payload)
        array = np.asarray(frame)
        if dtype is not None:
            array = array.astype(dtype, copy=False)
        return array

    def disconnect_camera(self) -> Dict[str, Any]:
        """Disconnect the camera sidecar."""
        return dict(self.call("disconnect_sidecar"))

    @property
    def max_signal(self) -> float:
        """Return the maximum digital count supported by this camera."""
        return 255.0

    def close(self) -> None:
        """Disconnect the camera and underlying HTTP session."""
        try:
            self.disconnect_camera()
        finally:
            self.disconnect()
