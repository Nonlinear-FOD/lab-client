"""Prototype scaffolding for remote S2 measurements.

This module wires together the existing device clients (laser, camera, etc.)
so you can orchestrate a full S2 sequence across multiple lab servers. It keeps
the logic deliberately thin for now—just enough to connect, grab a frame, and
plug in laser steps—so you can iterate quickly before porting the GUI.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Protocol

import numpy as np

from clients.chameleon_client import ChameleonClient
from clients.laser_clients import (
    AgilentLaserClient,
    AndoLaserClient,
    TiSapphireClient,
)
from clients.thorlabs_camera_client import ThorlabsCameraClient


@dataclass
class DeviceEndpoint:
    """Minimal info needed to instantiate a remote device client."""

    base_url: str
    device_name: str
    user: str | None = None
    init_kwargs: Dict[str, Any] = field(default_factory=dict)


class CameraProtocol(Protocol):
    def grab_frame(self) -> np.ndarray: ...
    def close(self) -> None: ...


class LaserProtocol(Protocol):
    @property
    def wavelength(self) -> float: ...

    @wavelength.setter
    def wavelength(self, value: float) -> None: ...

    def enable(self) -> None: ...
    def disable(self) -> None: ...
    def close(self) -> None: ...


@dataclass
class S2ScanConfig:
    """Parameters describing a wavelength sweep."""

    start_nm: float
    stop_nm: float
    step_nm: float
    settle_s: float = 0.2
    averages: int = 1  # grab N frames per wavelength and average

    def wavelengths(self) -> Iterable[float]:
        if self.step_nm == 0:
            raise ValueError("step_nm must be non-zero")
        count = int(round((self.stop_nm - self.start_nm) / self.step_nm)) + 1
        for idx in range(max(1, count)):
            yield self.start_nm + idx * self.step_nm


@dataclass
class S2RemoteSetup:
    """Composable orchestrator for S2 experiments using remote instruments."""

    camera: DeviceEndpoint
    laser: DeviceEndpoint
    camera_kind: str = "chameleon"  # or "thorlabs"
    laser_kind: str = "ando"  # or "agilent", "tisa"
    _cam_client: CameraProtocol | None = field(init=False, default=None)
    _laser_client: LaserProtocol | None = field(init=False, default=None)

    # ------------------------------------------------------------------ connect/disconnect
    def connect(self) -> None:
        """Instantiate all configured clients."""
        self._cam_client = self._connect_camera(self.camera_kind)
        self._laser_client = self._connect_laser(self.laser_kind)
        self._enable_laser_output()

    def disconnect(self) -> None:
        """Close all live clients."""
        for client in (self._cam_client, self._laser_client):
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ camera helpers
    def _connect_camera(self, kind: str) -> CameraProtocol:
        if kind == "chameleon":
            return ChameleonClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
        if kind == "thorlabs":
            return ThorlabsCameraClient(
                self.camera.base_url,
                self.camera.device_name,
                user=self.camera.user,
                **self.camera.init_kwargs,
            )
        raise ValueError(f"Unsupported camera kind '{kind}'")

    def grab_frame(self) -> np.ndarray:
        """Fetch a frame from whichever camera is connected."""
        if self._cam_client is None:
            raise RuntimeError("Camera client not connected")
        return self._cam_client.grab_frame()

    # ------------------------------------------------------------------ laser helpers
    def _connect_laser(self, kind: str) -> LaserProtocol:
        factories = {
            "ando": AndoLaserClient,
            "agilent": AgilentLaserClient,
            "tisa": TiSapphireClient,
        }
        factory = factories.get(kind.lower())
        if factory is None:
            raise ValueError(f"Unsupported laser kind '{kind}'")
        return factory(
            self.laser.base_url,
            self.laser.device_name,
            user=self.laser.user,
            **self.laser.init_kwargs,
        )

    def _enable_laser_output(self) -> None:
        if self._laser_client is not None and hasattr(self._laser_client, "enable"):
            try:
                self._laser_client.enable()  # type: ignore[attr-defined]
            except Exception:
                pass

    def _set_laser_wavelength(self, wavelength_nm: float) -> None:
        laser = self._laser_client
        if laser is None:
            raise RuntimeError("Laser client not connected")
        if hasattr(laser, "wavelength"):
            setattr(laser, "wavelength", wavelength_nm)
            return
        if hasattr(laser, "set_wavelength"):
            laser.set_wavelength(wavelength_nm)  # type: ignore[attr-defined]
            return
        raise RuntimeError("Connected laser does not expose wavelength control")

    # ------------------------------------------------------------------ measurement skeleton
    def run_single_step(
        self,
        wavelength_nm: float,
        averages: int = 1,
        settle_s: float = 0.0,
    ) -> Dict[str, Any]:
        """Move laser, optionally wait, capture averaged frame, and return payload."""
        self._set_laser_wavelength(wavelength_nm)
        if settle_s > 0:
            time.sleep(settle_s)
        frames: List[np.ndarray] = []
        for _ in range(max(1, int(averages))):
            frames.append(self.grab_frame())
        frame = frames[0] if len(frames) == 1 else np.mean(frames, axis=0)
        return {
            "wavelength_nm": wavelength_nm,
            "frame": frame,
        }

    def run_scan(self, config: S2ScanConfig) -> List[Dict[str, Any]]:
        """Execute an S2 sweep over the configured wavelength span."""
        results: List[Dict[str, Any]] = []
        for wl in config.wavelengths():
            result = self.run_single_step(
                wl,
                averages=config.averages,
                settle_s=config.settle_s,
            )
            results.append(result)
        return results
