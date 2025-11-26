# Photonetics Tunable Laser

- Client: `clients.laser_clients.PhotoneticsLaserClient`
- Server driver: `devices.laser_control.PhotoneticsLaser`
- Inherits tunable-laser helpers and power/OSA mixins documented in `devices/lasers/base.md`.

## Quickstart

```python
from clients.laser_clients import PhotoneticsLaserClient

base = "http://127.0.0.1:5000"
user = "alice"

laser = PhotoneticsLaserClient(
    base,
    "photonetics_laser_1",
    target_wavelength=1550.0,
    power=-5.0,
    GPIB_address=10,
    GPIB_bus=0,
    user=user,
)

laser.enable()
laser.wavelength = 1549.75
laser.power = -3.0
laser.power_unit = "DBM"  # or "MW"
laser.close()
```

## Notes

- Uses the standard tunable-laser + power mixins (enable/disable, wavelength, power, OSA-assisted tuning).

## API Reference

::: clients.laser_clients.PhotoneticsLaserClient
    options:
      show_source: false
      members_order: source
