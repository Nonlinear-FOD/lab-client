from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(slots=True)
class PyCapture2CameraSettings:
    """Initialization parameters for the PyCapture2 sidecar.

    Any field left unset falls back to the defaults defined by the server’s
    sidecar configuration.
    """

    camera_kind: str | None = None
    index: int | None = None
    serial_number: int | None = None
    width: int | None = None
    height: int | None = None
    offset_x: int | None = None
    offset_y: int | None = None
    pixel_format: int | None = None
    mode: int | None = None
    flip_vertical: bool | None = None
    auto_start: bool | None = None

    def to_payload(self) -> Dict[str, Any]:
        """Convert the dataclass to a JSON-friendly dict."""
        payload: Dict[str, Any] = {}
        for field_name, value in asdict(self).items():
            if value is None:
                continue
            payload[field_name] = value
        return payload


# Backwards compatibility aliases
ChameleonCameraSettings = PyCapture2CameraSettings
SpiriconCameraSettings = PyCapture2CameraSettings


@dataclass(slots=True)
class BobcatCameraSettings:
    """Initialization parameters for the Bobcat CVB sidecar."""

    driver_path: str | None = None
    exposure_time_us: float | None = None
    gain_value: float | None = None
    offset_value: int | None = None
    cooling_target_c: float | None = None
    timeout_ms: int | None = None
    auto_start: bool | None = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for field_name, value in asdict(self).items():
            if value is None:
                continue
            payload[field_name] = value
        return payload


@dataclass(slots=True)
class CameraWindow:
    """Rectangular region (in pixels) that can be cropped from a camera frame."""

    x_start: int
    x_end: int
    y_start: int
    y_end: int

    def to_payload(self) -> Dict[str, int]:
        """Return a JSON-friendly dict for HTTP payloads."""
        return {
            "x_start": int(self.x_start),
            "x_end": int(self.x_end),
            "y_start": int(self.y_start),
            "y_end": int(self.y_end),
        }
