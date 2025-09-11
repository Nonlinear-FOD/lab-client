# Ti:Sapphire Laser

- Client: `clients.laser_clients.TiSapphireClient`
- Server driver: `devices.tisa_control.TiSapphire`

## Quickstart

```python
from clients.laser_clients import TiSapphireClient

base = "http://127.0.0.1:5000"
tisa = TiSapphireClient(base, "tisa", com_port=5, user="alice")
tisa.wavelength = 800.0
tisa.close()
```

## Notes

- If no calibration is present, open-loop moves use `nm_to_pos_slope`.
- Use `calibrate(...)` with an OSA to build a position↔wavelength map.

## API Reference

::: clients.laser_clients.TiSapphireClient
    options:
      show_source: false
      members_order: source

