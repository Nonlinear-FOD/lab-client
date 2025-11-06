# Ando OSA

The OSA client provides high-level control for sweeping and reading spectral data.

- Client: `clients.osa_clients.OSAClient`
- Server driver: `devices.osa_control.OSA`

## Quickstart

```python
from clients.osa_clients import OSAClient

base = "http://127.0.0.1:5000"  # sim server
user = "alice"
osa = OSAClient(base, "osa_1", span=(1549, 1551), resolution=0.05, user=user)
osa.sweeptype = "SGL"
osa.sweep()
wl = osa.wavelengths  # numpy array
p = osa.powers        # numpy array (same shape)
osa.close()           # releases lock and drops server instance
```

## Common Operations

- Configure span: `osa.span = (start_nm, stop_nm)` or set at init.
- Resolution: `osa.resolution = 0.05` (nm).
- Sensitivity: `osa.sensitivity = "SMID"`.
- Sweep type: `osa.sweeptype = "SGL" | "RPT"`.
- Acquire: `osa.sweep()` then read `osa.wavelengths`, `osa.powers`.
- Traces: `osa.trace = "A" | "B" | "C"`; use `display_trace`, `blank_trace`, `write_trace`, `fix_trace`.

## Notes

- Arrays returned as numpy.
- Use `.close()` or `.disconnect()` to ensure a fresh instance on next connect.
- For troubleshooting, instantiate with `debug=True` to get detailed server errors.

## API Reference

::: clients.osa_clients.OSAClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source

