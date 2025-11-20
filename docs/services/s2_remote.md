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

camera_server = "http://10.0.0.5:5000"
laser_server = "http://10.0.0.6:5000"
camera_name = "bobcat_camera"
laser_name = "ando_laser_1"
user = "alice"
laser_kwargs = {"target_wavelength": 1550, "power": 0, "GPIB_bus": 0}

camera = DeviceEndpoint(camera_server, camera_name, user=user)
laser = DeviceEndpoint(laser_server, laser_name, user=user, init_kwargs=laser_kwargs)
setup = S2RemoteSetup(camera=camera, laser=laser, laser_kind="ando")
if not setup.is_connected:
    setup.connect()
#%%
scan = S2ScanConfig(start_nm=1548.0, stop_nm=1552.0, step_nm=0.1, averages=5)
window = S2ImageWindow(offset_x=60, offset_y=80, width=220, height=220)
processing = S2ProcessingConfig(
    window=window,
    output_pixels=64,
    background_frames=5,
    transform="linear",
)
run_measurement = False  # flip to True once the rectangle looks good
if not run_measurement:
    setup.live_preview(processing=processing, frame_averages=scan.averages)
else:
    result = setup.run_processed_scan(scan, processing, save_path="scan_cube.npz")
    setup.disconnect()
    print(f"{result.cube.shape[0]} steps captured into {result.cube.shape[1:]} bins")

```

## Key Concepts

- **camera_kind** — choose `"chameleon"`, `"spiricon"`, `"bobcat"`, or `"thorlabs"`; the setup instantiates the matching client and auto-starts capture.
- **DeviceEndpoint** — bundles base URL, device name, optional `user`, and client-specific kwargs (such as camera `settings`).
- **S2ImageWindow** — describes the rectangle you draw on the *full* live preview via `(offset_x, offset_y, width, height)`. The server crops exactly that region before it performs the requested `output_pixels` binning, so you get the bandwidth win without touching the hardware ROI.
- **Server-side binning** — `processing.output_pixels` is always honored on the server; the client never performs local binning/cropping, which keeps transfers small even over high-latency links.
- **Frame API** — both `S2RemoteSetup.grab_frame()` and `run_single_step()` return an `(array, overflow)` pair so callers can react to saturation immediately.
- **Overflow tracking** — every `grab_frame` now returns `(frame, overflow)` and `run_single_step`/scan metadata record when the camera reports sensor saturation.
- **Live preview flag** — `S2ScanConfig.live_preview` (defaults to `True`) opens a Matplotlib window while `run_scan()`/`run_processed_scan()` stream data so you can monitor max counts and catch overloads in real time. Set it to `False` for headless jobs.

## Live Preview

`S2RemoteSetup.live_preview()` streams the raw frame until you close the Matplotlib window or press `Ctrl+C`. The rectangle from `processing.window` is drawn on top, so you can tweak offsets and rerun the preview as many times as you like without reconnecting. Once you’re happy, simply set `run_measurement = True` (or call `run_processed_scan` directly) and reuse the same `processing` object—the server will crop/bin that exact region before sending frames back. There’s no prompt inside the loop; closing the figure returns you to the script immediately.

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
