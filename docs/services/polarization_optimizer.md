# Polarization Optimizer Service

High-level routines for optimizing polarization using an MPC320 and a fast ADC/PM.

- Client: `clients.polarization_optimizer_client.PolarizationOptimizerClient`
- Server driver: `devices.pol_opt_service.PolarizationOptimizer`

## Quickstart

```python
from clients.polarization_optimizer_client import PolarizationOptimizerClient

base = "http://127.0.0.1:5000"
svc = PolarizationOptimizerClient(base, "pol_opt")

# Continuous move + monitor
svc.move_and_monitor(mpc_device="mpc320_1", pm_device="arduino_adc", paddle_num=1, start_pos=0, end_pos=165.9)

# Brute-force (continuous scanning per paddle)
svc.brute_force_optimize(mpc_device="mpc320_1", pm_device="arduino_adc", start_pos=0, end_pos=165.9, step_size=1.0)

# Multiple controllers until tolerance
svc.optimize_multiple_pol_cons(
    pm_device="arduino_adc",
    mpc_a_device="mpc320_1",
    tolerance=0.01,
)
```

## Notes

- Device arguments are device names; the server resolves to live instances.
- `step_size` is accepted for compatibility but ignored (continuous scanning is used).

