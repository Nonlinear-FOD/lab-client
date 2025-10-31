# Tektronix Oscilloscope

High-level client for the generic Tektronix-style oscilloscope driver.

- Client: `clients.oscilloscope_client.OscilloscopeClient`
- Server driver: `devices.tektronix_oscilloscope.TektronixOscilloscope`

## Quickstart

```python
from clients.oscilloscope_client import OscilloscopeClient

base_url = "http://127.0.0.1:5000"  # lab-server URL
scope = OscilloscopeClient(
    base_url,
    "oscilloscope_1",
    host="192.168.1.50",          # or connection_resource / gpib_address
    channel=1,
    user="alice",
    debug=True,
)

# Adjust timebase and vertical settings
scope.time_scale = 5e-9     # seconds/div
scope.vertical_scale = 0.5  # volts/div
scope.offset = 0.0          # volts

# Capture the currently displayed waveform
times, volts, meta = scope.read_waveform()
print(times[:5], volts[:5])

scope.close()
```

## Common Operations

- Active channel: `scope.channel` (1-based). All getters/setters act on the active channel.
- Timebase controls:
  - `time_scale` (seconds/division)
  - `position` (horizontal delay)
  - `sample_rate`
  - `resolution` (sample count)
- Vertical controls: `vertical_scale` (volts/div) and `offset` (volts).
- Waveform acquisition: `times, volts, meta = scope.read_waveform()` returns numpy arrays (seconds/volts) plus the Tektronix scaling metadata (`XINCR`, `YZERO`, etc.).
- Pass `encoding="ASCII"` explicitly if you reconfigure DATA:ENCdg on the scope. Binary encodings can be added later.

## Notes

- The server driver derives transport automatically from `connection_resource`, `host`, or `gpib_address`.
- `read_waveform()` re-queries `WFMOutpre` every time to align scaling with the on-screen trace.
- Call `scope.close()` (or `.disconnect()`) to drop the server-side instance and release resource locks.

## API Reference

::: clients.oscilloscope_client.OscilloscopeClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
