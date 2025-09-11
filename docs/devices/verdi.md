# Verdi Laser

- Client: `clients.laser_clients.VerdiLaserClient`
- Server driver: `devices.verdi_laser.VerdiLaser`

## Quickstart

```python
from clients.laser_clients import VerdiLaserClient

base = "http://127.0.0.1:5000"
verdi = VerdiLaserClient(base, "verdi", com_port=12, user="alice")
verdi.standby_on()
print(verdi.power)
verdi.active_on()
verdi.power = 5.0
verdi.close()
```

## Notes

- Low-level port controls are exposed for troubleshooting (`port_*`).
- Shutter and power are exposed as properties.

## API Reference

::: clients.laser_clients.VerdiLaserClient
    options:
      show_source: false
      members_order: source

