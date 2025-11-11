# Chameleon Camera

Sidecar-backed control of legacy FLIR/Point Grey Chameleon cameras via the PyCapture2 SDK.

- Client: `clients.chameleon_client.ChameleonClient`
- Server proxy: `devices.chameleon_proxy.ChameleonProxy`
- Sidecar: `lab-server/sidecars/chameleon/camera_server.py`

## Quickstart

```python
from clients.chameleon_client import ChameleonClient

camera_server_url = "http://127.0.0.1:5000"
camera_name = "chameleon_camera"
user = "alice"

cam = ChameleonClient(
    camera_server_url,
    camera_name,
    user=user,
    settings={"width": 640, "height": 480, "auto_start": True},
)
cam.start_capture()
frame = cam.grab_frame(averages=3)  # numpy array
cam.disconnect_camera()
cam.close()
```

## Common Operations

- `connect_camera(settings=...)` — push Format7 ROI, pixel format, or auto-start.
- `start_capture()` / `stop_capture()` — mirror the PyCapture2 streaming calls.
- `grab_frame(averages=N, window=..., output_pixels=M)` — request raw or server-binned frames; window expects pixel indices.
- `max_signal` — 8-bit cameras default to 255 digital counts (used for saturation checks).

## Notes

- The sidecar runs inside a Python 3.6 venv with PyCapture2 installed; verify the `.venv` exists on the Windows host before launching the main server.
- `window`/`output_pixels` arguments only apply when the server proxy exposes cropping/binning; otherwise crop locally on the returned NumPy arrays.
- Always call `disconnect_camera()` (or `close()`) to release the server-side lock so other users can connect.

## API Reference

::: clients.chameleon_client.ChameleonClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
