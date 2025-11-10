from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from clients.base_client import LabDeviceClient


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

    def grab_frame(self, averages: int = 1, dtype: np.dtype | None = None) -> np.ndarray:
        """Capture frame(s) with optional on-device averaging."""
        payload: Dict[str, Any] = {}
        if averages and int(averages) > 1:
            payload["averages"] = int(averages)
        frame = self.call("grab_frame", **payload)
        array = np.asarray(frame)
        if dtype is not None:
            array = array.astype(dtype, copy=False)
        return array

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
