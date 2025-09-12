"""
PicoScope 2000A usage examples:

- Drive AWG with a duty-cycle square waveform
- Drive AWG with a single square pulse
- Capture on Channel A, then Channel B (explicit commands)
"""

from __future__ import annotations

from clients.picoscope2000a_client import PicoScope2000AClient


BASE = "http://127.0.0.1:5000"
DEVICE = "picoscope2000a"
USER = "your-name"


def awg_duty_cycle_example() -> None:
    pico = PicoScope2000AClient(BASE, DEVICE, user=USER, debug=True)

    # AWG: 100 kHz, 10% duty, 2 Vpp, 0 V offset
    pico.awg_square_duty(frequency=100_000.0, duty_cycle=0.10, pk_to_pk_uv=2_000_000, offset_uv=0)

    # Scope: Channel A, DC, ±1 V; rising edge at 0 mV, auto after 100 ms
    pico.scope_configure_channel(channel=0, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
    pico.scope_configure_trigger(enabled=True, source_channel=0, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)

    out = pico.scope_capture(num_samples=4000, timebase=8)
    print("A: samples=", out["samples"], "overflow=", out["overflow"]) 

    pico.close()


def awg_single_pulse_example() -> None:
    pico = PicoScope2000AClient(BASE, DEVICE, user=USER, debug=True)

    # AWG: 100 kHz, pulse from 25% to 35% of period
    pico.awg_square_pulse(frequency=100_000.0, start_frac=0.25, end_frac=0.35, pk_to_pk_uv=2_000_000, offset_uv=0)

    # Free-run snapshot (no trigger)
    pico.scope_configure_channel(channel=0, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
    pico.scope_configure_trigger(enabled=False)
    out = pico.scope_capture(num_samples=4000, timebase=8)
    print("A (free-run): samples=", out["samples"]) 

    pico.close()


def capture_A_then_B_example() -> None:
    pico = PicoScope2000AClient(BASE, DEVICE, user=USER, debug=True)

    # Ensure some stimulus exists (optional)
    pico.awg_square_duty(frequency=100_000.0, duty_cycle=0.10, pk_to_pk_uv=2_000_000, offset_uv=0)

    # Channel A
    pico.scope_configure_channel(channel=0, enabled=True, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
    pico.scope_configure_trigger(enabled=True, source_channel=0, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)
    outA = pico.scope_capture(num_samples=2000, timebase=8)
    print("A: samples=", outA["samples"]) 

    # Disable A before switching to B
    pico.scope_configure_channel(channel=0, enabled=False, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)

    # Channel B
    pico.scope_configure_channel(channel=1, enabled=True, coupling_type=pico.Coupling.DC, channel_range=pico.Range.V1)
    pico.scope_configure_trigger(enabled=True, source_channel=1, threshold_mv=0.0, direction=pico.Direction.RISING, auto_trigger_ms=100)
    outB = pico.scope_capture(num_samples=2000, timebase=8)
    print("B: samples=", outB["samples"]) 

    pico.close()


if __name__ == "__main__":
    awg_duty_cycle_example()
    awg_single_pulse_example()
    capture_A_then_B_example()

