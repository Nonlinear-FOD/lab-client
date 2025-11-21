from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class CameraROI:
    """Helper describing a rectangular ROI for on-device configuration."""

    width: int | None = None
    height: int | None = None
    offset_x: int | None = None
    offset_y: int | None = None
    native: bool | None = None

    def to_payload(self) -> dict[str, int | bool]:
        """Return a JSON-friendly payload skipping ``None`` fields."""
        payload: dict[str, int | bool] = {}
        for key, value in asdict(self).items():
            if value is None:
                continue
            if key == "native":
                payload[key] = bool(value)
            else:
                payload[key] = int(value)
        return payload


ROI_FIELDS = ("width", "height", "offset_x", "offset_y", "native")


def build_roi_payload(
    roi: CameraROI | Mapping[str, Any] | None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, int | bool]:
    """Merge ROI dataclasses/mappings plus overrides into a JSON payload."""
    payload: dict[str, int | bool] = {}
    if roi is not None:
        if isinstance(roi, CameraROI):
            payload.update(roi.to_payload())
        elif isinstance(roi, Mapping):
            for key in ROI_FIELDS:
                if key not in roi:
                    continue
                value = roi[key]
                if value is None:
                    continue
                payload[key] = bool(value) if key == "native" else int(value)
        else:
            raise TypeError("ROI must be a CameraROI or mapping")
    if overrides:
        for key, value in overrides.items():
            if key not in ROI_FIELDS:
                raise ValueError(f"Unsupported ROI field '{key}'")
            if value is None:
                continue
            payload[key] = bool(value) if key == "native" else int(value)
    return payload


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
    native: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        """Convert the dataclass to a JSON-friendly dict."""
        payload: dict[str, Any] = {}
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
    width: int | None = None
    height: int | None = None
    offset_x: int | None = None
    offset_y: int | None = None
    native: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
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

    def to_payload(self) -> dict[str, int]:
        """Return a JSON-friendly dict for HTTP payloads."""
        return {
            "x_start": int(self.x_start),
            "x_end": int(self.x_end),
            "y_start": int(self.y_start),
            "y_end": int(self.y_end),
        }
