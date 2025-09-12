# Keithley 2700

Minimal client for the Keithley 2700 Multimeter/Switch System.

- Client: `clients.keithley2700_client.Keithley2700Client`
- Server driver: `devices.keithley_2700.Keithley2700`

## Quickstart

```python
from clients.keithley2700_client import Keithley2700Client

base = "http://127.0.0.1:5000"
km = Keithley2700Client(base, "keithley_2700", GPIB_bus=0, GPIB_address=16, user="alice", debug=True)

# Assumes function/range/resolution are set on the instrument front panel
v = km.read_voltage()
print("Voltage:", v)

km.close()
```

## Notes

- The driver does not change instrument settings. It only issues `FETCh?` and parses the first numeric field.
- Configure function, range, and resolution manually (e.g., DCV) on the meter before calling `read_voltage()`.

## API Reference

::: clients.keithley2700_client.Keithley2700Client
    options:
      show_source: false
      show_root_heading: true
      members_order: source
