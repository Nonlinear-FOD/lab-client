from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import CameraWindow


class ThorlabsCameraClient(LabDeviceClient):
    """Client for the uc480-based Thorlabs camera driver."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        self._initialize_device(kwargs)

    def grab_frame(
        self,
        averages: int = 1,
        dtype: np.dtype | None = None,
        window: CameraWindow | Dict[str, int] | None = None,
        output_pixels: int | None = None,
    ) -> Tuple[np.ndarray, bool]:
        """Capture frame(s) plus overflow flag with optional averaging/cropping/binning."""
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

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the current frame shape."""
        val = self.get_property("shape")
        if isinstance(val, (list, tuple)) and len(val) == 2:
            return int(val[0]), int(val[1])
        raise RuntimeError("Unexpected shape response from server")

    @property
    def max_signal(self) -> int:
        """Maximum digital value for the current pixel format."""
        return int(self.get_property("max_signal"))

    def close(self) -> None:
        try:
            self.call("close")
        finally:
            self.disconnect()
