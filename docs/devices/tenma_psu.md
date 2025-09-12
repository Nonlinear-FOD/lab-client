# Tenma 72-26xx DC Power Supply

High-level client for Tenma dual-channel DC power supplies (e.g., 72-2645).

- Client: `clients.tenma_psu_client.TenmaPSUClient`
- Server driver: `devices.tenma_dc_p_supply.TenmaDCPowerSupply`

## Quickstart

```python
from clients.tenma_psu_client import TenmaPSUClient

base = "http://127.0.0.1:5000"
psu = TenmaPSUClient(base, "tenma_psu", com_port="/dev/ttyUSB0", user="alice", debug=True)

# Select channel and set setpoints
psu.channel = 1
psu.voltage_set = 5.00
psu.current_set = 0.50

# Enable output and read back actual values
psu.output = True
v = psu.voltage
i = psu.current

# Switch to CH2 and configure
psu.channel = 2
psu.voltage_set = 12.00
psu.current_set = 0.25

# Check status and turn output off
print(psu.status())
psu.output = False
psu.close()
```

## Notes

- Channel selection: use `psu.channel` (1 or 2). All set/get properties act on the active channel.
- Properties:
  - `voltage_set` (V) — read/write setpoint
  - `voltage` (V) — read-only actual
  - `current_set` (A) — read/write setpoint
  - `current` (A) — read-only actual
  - `output` — global output state (True/False)
- Front panel helpers: `psu.lock(True/False)`, `psu.beep(True/False)`.
- Memory recall: `psu.recall(slot)` for slot 1..5.

## API Reference

::: clients.tenma_psu_client.TenmaPSUClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
