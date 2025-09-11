# Agilent Tunable Laser

- Client: `clients.laser_clients.AgilentLaserClient`
- Server driver: `devices.laser_control.AgilentLaser`

## Quickstart

```python
from clients.laser_clients import AgilentLaserClient

base = "http://127.0.0.1:5000"
laser = AgilentLaserClient(base, "agilent_laser_1", target_wavelength=1550.0, power=0.0, source=1, user="alice")
laser.wavelength = 1549.8
laser.enable()
laser.power = 0.5
laser.close()
```

## Notes

- Set `source` to select the output channel for multi-source models.
- Use OSA-assisted helpers from the client for fine alignment.

## API Reference

::: clients.laser_clients.AgilentLaserClient
    options:
      show_source: false
      members_order: source

