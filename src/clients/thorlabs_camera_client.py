from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from clients.base_client import LabDeviceClient
from clients.camera_models import CameraROI, CameraWindow, build_roi_payload


class ThorlabsCameraClient(LabDeviceClient):
    """Client for the uc480-based Thorlabs camera driver."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        roi: CameraROI | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(base_url, device_name, user=user, debug=debug)
        init_payload = dict(kwargs)
        init_payload.update(build_roi_payload(roi))
        self._initialize_device(init_payload)

    def grab_frame(
        self,
        averages: int = 1,
        dtype: np.dtype | None = None,
        window: CameraWindow | dict[str, int] | None = None,
        output_pixels: int | None = None,
    ) -> tuple[np.ndarray, bool]:
        """Capture frame(s) plus overflow flag with optional averaging/cropping/binning."""
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

    def configure_roi(
        self,
        roi: CameraROI | Mapping[str, Any] | None = None,
        **overrides: Any,
    ) -> dict[str, int]:
        """
        Push a new hardware ROI to the uc480 driver.

        Args:
            roi: Optional :class:`CameraROI` definition.
            **overrides: Individual ROI fields (width/height/offset_x/offset_y/native).

        Returns:
            Dict containing the applied ``offset_x/offset_y/width/height``.
        """
        payload = build_roi_payload(roi, overrides)
        if not payload:
            raise ValueError("configure_roi requires at least one ROI parameter")
        result = self.call("configure_roi", **payload)
        if not isinstance(result, dict):
            raise RuntimeError("Server did not return ROI payload")
        return {
            "offset_x": int(result["offset_x"]),
            "offset_y": int(result["offset_y"]),
            "width": int(result["width"]),
            "height": int(result["height"]),
        }

    @property
    def shape(self) -> tuple[int, int]:
        """Return the current frame shape."""
        val = self.get_property("shape")
        if isinstance(val, (list, tuple)) and len(val) == 2:
            return int(val[0]), int(val[1])
        if hasattr(val, "__len__") and len(val) == 2:
            try:
                return int(val[0]), int(val[1])
            except Exception:
                pass
        if isinstance(val, dict):
            height = val.get("height")
            width = val.get("width")
            if height is not None and width is not None:
                return int(height), int(width)
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
