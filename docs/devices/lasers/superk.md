# NKTP SuperK Compact

- Client: `clients.superk_client.SuperKCompactClient`
- Server driver: `devices.nktp_superk_compact.SuperKCompact`

## Quickstart

```python
from clients.superk_client import SuperKCompactClient

base = "http://127.0.0.1:5000"
user = "alice"
laser = SuperKCompactClient(base, "nktp_superk_1", port=3, user=user)

# Toggle emission
laser.enable()
laser.emission = 0  # or use disable()

# Set repetition rate and output power
laser.reprate = 10_000        # Hz
laser.power_percentage = 50   # 0–100

laser.close()
```

## Notes

- `port` accepts an int (`3` -> `COM3`) or a string (`"COM4"`).
- `power_percentage` writes the underlying driver register directly (0–100).
- `reprate` is converted to a percentage internally using the driver’s max rep rate.

## API Reference

::: clients.superk_client.SuperKCompactClient
    options:
      show_source: false
      members_order: source
