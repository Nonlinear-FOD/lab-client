# Bobcat Camera

Sidecar-backed control of the Xenics Bobcat (CVB/GenICam) camera used in the S2 bench.

- Client: `clients.bobcat_client.BobcatClient`
- Server proxy: `devices.bobcat_proxy.BobcatProxy`
- Sidecar: `lab-server/sidecars/bobcat/camera_server.py`

## Quickstart

```python
from clients.bobcat_client import BobcatClient
from clients.camera_models import BobcatCameraSettings

camera_server_url = "http://127.0.0.1:5000"
camera_name = "bobcat_camera"
user = "alice"

settings = BobcatCameraSettings(
    exposure_time_us=5.0,
    gain_value=1.0,
    auto_start=True,
)

cam = BobcatClient(
    camera_server_url,
    camera_name,
    settings=settings,
    user=user,
)
cam.start_capture()
frame, overflow = cam.grab_frame(averages=4)
print(frame.shape, frame.dtype, overflow)
cam.disconnect_camera()
cam.close()
```

## Common Operations

- Use `BobcatCameraSettings` to override exposure, gain/offset, cooling target, or custom VIN path.
- `configure_roi(CameraROI(...))` — program the CVB AOI at runtime (use `native=True` to revert to the full sensor window).
- `grab_frame(averages=N, window=..., output_pixels=M)` returns `(frame, overflow)` so you can act immediately on sensor saturation that was detected server-side.
- `max_signal` still reflects the 16‑bit ADC (35300 counts) in case you need to set thresholds client-side.

## Notes

- The sidecar must run inside the Windows CVB `.venv` where `cvb` is installed and the GenICam driver (`drivers/GenICam.vin`) is accessible.
- If `.venv` is missing the server logs a warning and skips launching the sidecar; create it with Python 3.6 + CVB before starting the lab server.
- For stable acquisition leave the node map in manual offset/gain mode as configured by the sidecar helper.

## API Reference

::: clients.bobcat_client.BobcatClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
