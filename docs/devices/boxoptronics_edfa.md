# Box Optronics EDFA Amplifier

- Client: `clients.boxoptronics_edfa_client.BoxoptronicsEDFAClient`
- Server driver: `devices.boxoptronics_edfa.BoxoptronicsEDFA`

## Quickstart

```python
from clients.boxoptronics_edfa_client import BoxoptronicsEDFAClient

base = "http://127.0.0.1:5000"
user = "alice"
edfa = BoxoptronicsEDFAClient(base, "boxoptronics_edfa", com_port=3, user=user)
print(edfa.read_status())
edfa.enable()
edfa.target_power_dbm = 10.0
edfa.disable()
edfa.close()
```

## Notes

- Enabling/disabling respects device interlocks and safety conditions.
- Modes and limits depend on the specific model/configuration.

## API Reference

::: clients.boxoptronics_edfa_client.BoxoptronicsEDFAClient
    options:
      show_source: false
      members_order: source

