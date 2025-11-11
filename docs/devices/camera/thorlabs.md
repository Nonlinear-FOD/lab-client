# Thorlabs Camera

Driver for the uc480-based Thorlabs DCx industrial cameras hosted directly in the main server (no sidecar required).

- Client: `clients.thorlabs_camera_client.ThorlabsCameraClient`
- Server driver: `devices.thorlabs_camera.ThorlabsCamera`

## Quickstart

```python
from clients.thorlabs_camera_client import ThorlabsCameraClient

camera_server_url = "http://127.0.0.1:5000"
camera_name = "thorlabs_camera"
user = "alice"

cam = ThorlabsCameraClient(
    camera_server_url,
    camera_name,
    user=user,
)
frame = cam.grab_frame(averages=5)
print(cam.shape, cam.max_signal)
cam.close()
```

## Common Operations

- `grab_frame(averages=N, window=..., output_pixels=M)` — leverage on-device averaging/cropping/binning before frames are returned.
- `shape` — fetch the configured AOI dimensions for downstream processing.
- `max_signal` — use to guard against saturation (255 for Mono8, 65535 for Mono16).
- `close()` — shuts down the uc480 driver and releases the server-side instance.

## Notes

- The server must run on Windows with the Thorlabs/IDS uc480 `.NET` SDK installed; the driver loads `uc480DotNet.dll` from `C:\Program Files\Thorlabs\Scientific Imaging\DCx Camera Support\Develop\DotNet`.
- AOI and pixel format defaults match the legacy `cam_control.py` script but can be overridden in the server config before connecting.
- This client mirrors the API of the sidecar cameras so S2 tooling can swap between `"thorlabs"`, `"chameleon"`, and `"bobcat"` kinds.

## API Reference

::: clients.thorlabs_camera_client.ThorlabsCameraClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
