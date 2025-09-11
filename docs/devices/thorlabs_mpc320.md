# Thorlabs MPC320 Polarization Controller

- Client: `clients.thorlabs_mpc320_client.ThorlabsMPC320Client`
- Server driver: `devices.thorlabs_mpc320.ThorlabsMPC320`

## Quickstart

```python
from clients.thorlabs_mpc320_client import ThorlabsMPC320Client

base = "http://127.0.0.1:5000"
mpc = ThorlabsMPC320Client(base, "mpc320_1", user="alice")
mpc.velocity = 60
pos = mpc.get_position(1)
mpc.set_position(1, pos + 5.0)
mpc.close()
```

## Notes

- Motion calls are blocking on the server and accept a timeout.
- Use the Polarization Optimizer service for continuous move+monitor workflows.

