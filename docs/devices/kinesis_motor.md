# Thorlabs KCube DC Servo Motor

- Client: `clients.kinesis_motor_client.KinesisMotorClient`
- Server driver: `devices.kinesis_motor.KinesisMotor`

## Quickstart

```python
from clients.kinesis_motor_client import KinesisMotorClient

base = "http://127.0.0.1:5000"
kc = KinesisMotorClient(base, "kinesis_motor_1", user="alice")
kc.home()
kc.move_absolute(2.0)
kc.move_relative(-0.25)
print(f"Position: {kc.get_position():.3f} mm")
kc.close()
```

## Notes

- Distances are interpreted in millimetres; ensure the controller is using the correct stage file so real-world units map to device counts.
- Motion methods block until completion and accept an optional timeout.
- Use `stop()` to halt motion immediately if the axis needs to be interrupted.

## API Reference

::: clients.kinesis_motor_client.KinesisMotorClient
    options:
      show_source: false
      members_order: source
