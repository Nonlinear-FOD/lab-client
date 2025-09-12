# Zaber 1D Motor

Minimal client for a single-axis Zaber Motion stage (via `zaber_motion`).

- Client: `clients.zaber_1d_client.Zaber1DMotorClient`
- Server driver: `devices.zaber_1d_motor.Zaber1DMotor`

## Quickstart

```python
from clients.zaber_1d_client import Zaber1DMotorClient

base = "http://127.0.0.1:5000"
motor = Zaber1DMotorClient(base, "zaber_1d", com_port=3, units="mm", user="alice", debug=True)

motor.home()              # home if needed
motor.move_relative(5.0)  # move +5 mm

motor.units = "um"
motor.move_relative(500)  # +500 µm

motor.close()
```

## Units

Set or read the units with the `units` property. Accepted values:

- `native`, `m`, `cm`, `mm`, `um`/`µm`, `nm`, `in`

## API Reference

::: clients.zaber_1d_client.Zaber1DMotorClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
