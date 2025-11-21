from __future__ import annotations

from typing import Any

from clients.camera_models import ChameleonCameraSettings
from clients.pycapture2_client import PyCapture2Client


class ChameleonClient(PyCapture2Client):
    """Legacy alias that pins :class:`PyCapture2Client` to Chameleon defaults."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        settings: ChameleonCameraSettings | None = None,
        auto_connect: bool = True,
        max_signal: float | None = None,
        camera_kind: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url,
            device_name,
            user=user,
            debug=debug,
            settings=settings,
            auto_connect=auto_connect,
            camera_kind=camera_kind,
            max_signal=max_signal,
            **kwargs,
        )
