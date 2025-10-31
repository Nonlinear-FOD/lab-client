# Polarization Optimizer Service

High-level routines for optimizing polarization using an MPC320 and a fast ADC/PM.

- Client: `clients.polarization_optimizer_client.PolarizationOptimizerClient`
- Server driver: `devices.pol_opt_service.PolarizationOptimizer`
- Note: unlike hardware clients, this service represents orchestration logic that
  runs on the server and composes other devices.

## Quickstart

```python
from clients.polarization_optimizer_client import PolarizationOptimizerClient
from clients.thorlabs_mpc320_client import ThorlabsMPC320Client
from clients.arduino_adc_client import ArduinoADCClient

base = "http://127.0.0.1:5000"
user = "alice"
pol_opt = PolarizationOptimizerClient(base, "pol_opt")
mpc = ThorlabsMPC320Client(base, "mpc320_1", user=user)
adc = ArduinoADCClient(base, "arduino_adc", user=user)

# Continuous move + monitor (accepts device names or client objects)
pol_opt.move_and_monitor(mpc_device=mpc, pm_device=adc, paddle_num=1, start_pos=0, end_pos=165.9)

# Brute-force (continuous scanning per paddle)
pol_opt.brute_force_optimize(mpc_device=mpc, pm_device=adc, start_pos=0, end_pos=165.9)

# Multiple controllers until tolerance
pol_opt.optimize_multiple_pol_cons(
    pm_device=adc,
    mpc_a_device=mpc,
    tolerance=0.01,
)
```

## Notes

- Device arguments can be device names or client objects; the service extracts
  `device_name` when objects are passed.
- `PolarizationOptimizerClient` represents a *logical* service hosted on the
  server. It does not map to a single piece of hardware; instead it remotely
  drives connected MPC/ADC devices using server-side control loops. That is why
  it omits a `user` lock by default and has no direct hardware state.

## API Reference

::: clients.polarization_optimizer_client.PolarizationOptimizerClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
