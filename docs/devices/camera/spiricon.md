# Spiricon Camera

Sidecar-backed control of Spiricon cameras via the shared PyCapture2 SDK stack.

- Client: `clients.spiricon_client.SpiriconClient`
- Server proxy: `devices.pycapture2_proxy.PyCapture2Proxy` (with `camera_kind="spiricon"`)
- Sidecar: `lab-server/sidecars/pycapture2/server.py`

## Quickstart

```python
from clients.camera_models import PyCapture2CameraSettings
from clients.spiricon_client import SpiriconClient

camera_server_url = "http://127.0.0.1:5000"
camera_name = "spiricon_camera"
user = "alice"

settings = PyCapture2CameraSettings(
    width=1280,
    height=1024,
    auto_start=True,
)
cam = SpiriconClient(camera_server_url, camera_name, user=user, settings=settings)
cam.start_capture()
frame, overflow = cam.grab_frame(averages=3)  # numpy array + saturation flag
cam.disconnect_camera()
cam.close()
```

## Common Operations

- `connect_camera(settings=...)` — push Format7 ROI, pixel format, serial binding, or auto-start options.
- `start_capture()` / `stop_capture()` — mirror the PyCapture2 streaming calls.
- `grab_frame(averages=N, window=..., output_pixels=M)` — request raw or server-binned frames; returns `(frame, overflow)` to reflect hardware saturation.
- `max_signal` — defaults to 65 535 digital counts for 16-bit operation but can be overridden per setup.

## Notes

- The sidecar runs inside a Python 3.6 venv with PyCapture2 installed; verify the `.venv` exists on the Windows host before launching the main server.
- `window`/`output_pixels` arguments only apply when the server proxy exposes cropping/binning; otherwise crop locally on the returned NumPy arrays.
- Always call `disconnect_camera()` (or `close()`) to release the server-side lock so other users can connect.

## API Reference

::: clients.spiricon_client.SpiriconClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
