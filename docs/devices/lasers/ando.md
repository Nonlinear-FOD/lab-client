# Ando Tunable Laser

- Client: `clients.laser_clients.AndoLaserClient`
- Server driver: `devices.laser_control.AndoLaser`

## Quickstart

```python
from clients.laser_clients import AndoLaserClient

base = "http://127.0.0.1:5000"
laser = AndoLaserClient(base, "ando_laser_1", target_wavelength=1550.0, power=0.0, user="alice")
laser.wavelength = 1550.5
laser.enable()
laser.power = 1.0
laser.close()
```

## Notes

- Power units are device-dependent; see server driver config.
- Use `adjust_wavelength(...)` for OSA-assisted tuning (requires an OSA).

## API Reference

::: clients.laser_clients.AndoLaserClient
    options:
      show_source: false
      members_order: source

