---
title: Standa XIMC Motor
---

Client: `clients.standa_motor_client.StandaMotorClient`  
Server driver: `devices.standa_motor.StandaMotor` (`standa_motor` config)

## Setup
- The repo bundles the XIMC wrapper at `ximc-2.14.31/ximc/crossplatform/wrappers/python`.
- On Windows, install the Standa USB driver (`ximc-2.14.31/driver/Standa_8SMC4-5.inf`) so the controller appears as an XIMC device.
- Ensure the XIMC shared libs are on the loader path (e.g., add the appropriate `library-files/win64` or `.../debian-amd64` folder to PATH/LD_LIBRARY_PATH before running the server).
- The server config key is `standa_motor` (`lab-server/main_server/config/standa_motor.json`). Set `uri` there (e.g., `xi-com:\\\\.\\COM5`) or pass it from the client.

## Quickstart
```python
from clients.standa_motor_client import StandaMotorClient

base = "http://127.0.0.1:5000"
mot = StandaMotorClient(base, "standa_motor", uri=r"xi-com:\\\\.\\COM5")

print(mot.uri)                # active URI
print(mot.position)           # {'steps': ..., 'microsteps': ...}
mot.move_relative(10)         # move by 10 steps
mot.home(0)
mot.close()
```

## API surface
- Properties: `uri` (read), `position` (get/set dict with `steps`/`microsteps`), `speed` (get/set, controller units).
- Methods: `home()`, `move_absolute(steps, microsteps=0, wait_interval_ms=100)`, `move_relative(steps, microsteps=0, wait_interval_ms=100)`, `wait_for_stop(interval_ms=100)`, `stop()`, `close()`.

Notes:
- Units are the controller’s native steps/microsteps. If you need mm/deg, apply your stage’s scaling externally.
- If `enumerate_devices` returns empty on Windows, set `uri` explicitly to the COM port URI (`xi-com:\\\\.\\COM5`).
