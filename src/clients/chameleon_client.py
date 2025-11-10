from __future__ import annotations

from typing import Any, Dict

import numpy as np

from clients.base_client import LabDeviceClient


class ChameleonClient(LabDeviceClient):
    """Client for the Chameleon camera sidecar proxied through the main server."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        # The proxy itself only needs base_url/timeout from server config.
        # Still run connect to ensure the instance exists server-side.
        self._initialize_device(kwargs)

    def connect_camera(
        self,
        index: int | None = None,
        width: int | None = None,
        height: int | None = None,
        offset_x: int | None = None,
        offset_y: int | None = None,
        pixel_format: int | None = None,
        mode: int | None = None,
        flip_vertical: bool | None = None,
        auto_start: bool | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if index is not None:
            payload["index"] = int(index)
        if width is not None:
            payload["width"] = int(width)
        if height is not None:
            payload["height"] = int(height)
        if offset_x is not None:
            payload["offset_x"] = int(offset_x)
        if offset_y is not None:
            payload["offset_y"] = int(offset_y)
        if pixel_format is not None:
            payload["pixel_format"] = int(pixel_format)
        if mode is not None:
            payload["mode"] = int(mode)
        if flip_vertical is not None:
            payload["flip_vertical"] = bool(flip_vertical)
        if auto_start is not None:
            payload["auto_start"] = bool(auto_start)
        return dict(self.call("connect_sidecar", **payload))

    def start_capture(self) -> Dict[str, Any]:
        return dict(self.call("start_capture"))

    def stop_capture(self) -> Dict[str, Any]:
        return dict(self.call("stop_capture"))

    def grab_frame(self, averages: int = 1, dtype: np.dtype | None = None) -> np.ndarray:
        payload: Dict[str, Any] = {}
        if averages and int(averages) > 1:
            payload["averages"] = int(averages)
        frame = self.call("grab_frame", **payload)
        array = np.asarray(frame)
        if dtype is not None:
            array = array.astype(dtype, copy=False)
        return array

    def disconnect_camera(self) -> Dict[str, Any]:
        return dict(self.call("disconnect_sidecar"))

    def close(self) -> None:
        try:
            self.disconnect_camera()
        finally:
            self.disconnect()
