# PicoScope 2000A

High-level client for PicoScope 2000A series oscilloscopes with built‑in AWG.

- Client: `clients.picoscope2000a_client.PicoScope2000AClient`
- Server driver: `devices.picoscope2000a.PicoScope2000A`

## Quickstart

```python
from clients.picoscope2000a_client import PicoScope2000AClient

base = "http://127.0.0.1:5000"
user = "alice"
pico = PicoScope2000AClient(base, "picoscope2000a", user=user, debug=True)

# Option 1 — Drive AWG with duty‑cycle square wave (10% duty at 100 kHz)
pico.awg_square_duty(frequency=100_000.0, duty_cycle=0.10, pk_to_pk_uv=2_000_000, offset_uv=0)

# Option 2 — Drive AWG with a single square pulse per period (25%–35% window)
# pico.awg_square_pulse(frequency=100_000.0, start_frac=0.25, end_frac=0.35, pk_to_pk_uv=2_000_000, offset_uv=0)

# Configure scope (Channel A, DC, ±1 V range)
pico.scope_configure_channel(channel=0, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)

# Trigger on Channel A, mid‑level, rising edge; auto‑trigger after 100 ms
pico.scope_configure_trigger(enabled=True, source_channel=0, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)

# Acquire one block
out = pico.scope_capture(num_samples=5000, timebase=8)
t_us, mV = out["time_us"], out["mV"]

pico.close()
```

## Usage Notes and Quirks

- Order matters: configure the input channel first, then the trigger, then call `scope_capture`.
- Triggers control when acquisition starts; they do not change the captured waveform shape. For quick snapshots, disable the trigger or keep a nonzero `auto_trigger_ms`.
- One channel per capture: the current server driver returns data for the last configured channel only. To measure both A and B, run two captures sequentially.

### Measuring Channel A then Channel B (explicit commands)

```python
# Channel A (enable, trigger on A, capture)
pico.scope_configure_channel(channel=0, enabled=True, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
pico.scope_configure_trigger(enabled=True, source_channel=0, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)
outA = pico.scope_capture(num_samples=2000, timebase=8)

# Disable A before switching to B
pico.scope_configure_channel(channel=0, enabled=False, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)

# Channel B (enable, trigger on B, capture)
pico.scope_configure_channel(channel=1, enabled=True, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
pico.scope_configure_trigger(enabled=True, source_channel=1, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)
outB = pico.scope_capture(num_samples=2000, timebase=8)
```

### Free‑Run Snapshot (no trigger)

```python
# Disable triggering entirely for a quick snapshot
pico.scope_configure_trigger(enabled=False)
out = pico.scope_capture(num_samples=2000, timebase=8)
```

## Enum Options

Options are exposed on the client: `pico.WaveType`, `pico.Coupling`, `pico.Range`, `pico.Direction`, `pico.RatioMode`.

```python
pico.print_options()           # human‑readable
opts = pico.list_options()     # programmatic dict
```

## API Reference

::: clients.picoscope2000a_client.PicoScope2000AClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
