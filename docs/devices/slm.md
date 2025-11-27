# SLM (SLMDisplay)

Client: `clients.slm_client.SLMClient`  
Server driver: `devices.slm_display.SLMDisplay`

- Connect with the device name from server config (e.g., `slm_1`, `slm_2`).
- Calibration auto-loads from the server’s `devices/calibration_data/SLM/<slm_id>/` (no client-side calibration calls needed).
- Display selection: if `monitor_display` is unset, the server picks the monitor whose desktop size is closest to the calibration/image size; otherwise set `monitor_display` explicitly.

## Typical usage (bulk settings)

```python
from clients.slm_client import SLMClient

slm = SLMClient("http://127.0.0.1:5000", "slm_1")

# Set all knobs in one shot via the bulk settings dict
slm.settings = {
    "wavelength_nm": 1550,
    "oam_L_num": 5,
    "lp_m_num": 0,
    "lp_l_num": 0,
    "tilt": 0.0,
    "lens_mm": 0.0,
    "x_offset": 0,
    "y_offset": 0,
    "diameter": 1000,
    "rotation_pi": 0,
    "attenuation": False,
}

# Render to the SLM and fetch the preview (8-bit ndarray)
resp = slm.render(return_preview=True)
preview = resp["preview"]
```

Other actions:
- `clear()`
- Individual knob properties are also exposed if you prefer to set them one by one (e.g., `slm.wavelength_nm = 1550`).
