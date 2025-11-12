from __future__ import annotations

from typing import Any

from clients.camera_models import SpiriconCameraSettings
from clients.pycapture2_client import PyCapture2Client


class SpiriconClient(PyCapture2Client):
    """Thin wrapper that pins :class:`PyCapture2Client` to Spiricon defaults."""

    def __init__(
        self,
        base_url: str,
        device_name: str,
        user: str | None = None,
        debug: bool = False,
        settings: SpiriconCameraSettings | None = None,
        auto_connect: bool = True,
        max_signal: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url,
            device_name,
            user=user,
            debug=debug,
            settings=settings,
            auto_connect=auto_connect,
            camera_kind="spiricon",
            max_signal=max_signal,
            **kwargs,
        )
