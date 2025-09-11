# Thorlabs PM100 Power Meter

- Client: `clients.thorlabs_pm_client.ThorlabsPMClient`
- Server driver: `devices.thorlabs_pm.ThorlabsPM`

## Quickstart

```python
from clients.thorlabs_pm_client import ThorlabsPMClient

base = "http://127.0.0.1:5000"
pm = ThorlabsPMClient(base, "thorlabspm_1", user="alice")
pm.wavelength = 1550.0
pm.scale = "log"   # dBm
print(pm.read())
pm.close()
```

## Notes

- `scale='lin'` returns Watts; `'log'` returns dBm.
- VISA resource must be accessible on the server host.

## API Reference

::: clients.thorlabs_pm_client.ThorlabsPMClient
    options:
      show_source: false
      members_order: source

