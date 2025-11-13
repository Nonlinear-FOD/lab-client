# S2 Remote Orchestrator

High-level helper that ties together a tunable laser and camera client to reproduce the legacy S2 measurement flow over HTTP.

- Module: `setups.s2_remote`
- Core class: `setups.s2_remote.S2RemoteSetup`
- Supporting dataclasses: `DeviceEndpoint`, `S2ScanConfig`, `S2ImageWindow`, `S2ProcessingConfig`

## Quickstart

```python
from setups.s2_remote import (
    DeviceEndpoint,
    S2RemoteSetup,
    S2ScanConfig,
    S2ImageWindow,
    S2ProcessingConfig,
)

camera_server_url = "http://127.0.0.1:5000"
laser_server_url = "http://127.0.0.1:5000"
camera_name = "bobcat_camera"
laser_name = "ando_laser_1"
user = "alice"
laser_init_kwargs = {"target_wavelength": 1550, "power": 0, "GPIB_bus": 0}

camera = DeviceEndpoint(
    base_url=camera_server_url,
    device_name=camera_name,
    user=user,
    init_kwargs={"settings": {"auto_start": True}},
)
laser = DeviceEndpoint(
    base_url=laser_server_url,
    device_name=laser_name,
    user=user,
    init_kwargs=laser_init_kwargs,
)

setup = S2RemoteSetup(
    camera=camera,
    laser=laser,
    laser_kind="ando",
)

scan = S2ScanConfig(start_nm=1548.0, stop_nm=1552.0, step_nm=0.1, averages=5)
processing = S2ProcessingConfig(
    window=S2ImageWindow(0, 800, 0, 800),
    output_pixels=64,
    background_frames=5,
    server_binning=True,
)

setup.connect()
result = setup.run_processed_scan(scan, processing, save_path="scan_cube.npz")
setup.disconnect()
print(result.relative_power_db)
```

## Key Concepts

- **camera_kind** — choose `"chameleon"`, `"spiricon"`, `"bobcat"`, or `"thorlabs"`; the setup instantiates the matching client and auto-starts capture.
- **DeviceEndpoint** — bundles base URL, device name, optional `user`, and client-specific kwargs (such as camera `settings`).
- **Server binning** — set `processing.server_binning=True` to offload cropping/binning to the camera proxy; otherwise frames are processed locally after download.
- **Safety checks** — saturation warnings rely on each client’s `max_signal` (255 for Chameleon, 65 535 for Spiricon, 35 300 for Bobcat).

## Tips

- Call `capture_background()` to obtain a fresh reference frame whenever the bench drifts.
- `run_single_step()` is handy for scripting quick manual shots without a full sweep.
- The resulting `S2ScanResult` provides helpers to save either the modern `.npz` format (`save_npz`) or legacy GUI `.npy` layout (`save_legacy_npy`).

## API Reference

::: setups.s2_remote.S2RemoteSetup
    options:
      show_source: false
      show_root_heading: true
      members_order: source
