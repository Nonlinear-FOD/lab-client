# Overview

Read-only endpoints to inspect connected devices and locks, and to enumerate VISA resources.

- Client: `clients.lab_overview_client.LabOverviewClient`

## Quickstart

```python
from clients.lab_overview_client import LabOverviewClient

base = "http://127.0.0.1:5000"
user = "alice"
view = LabOverviewClient(base, user=user)
print(view.devices())            # connection + lock summary
print(view.list_used_instruments())
print(view.list_connected_instruments(probe_idn=True))
```

## API Reference

::: clients.lab_overview_client.LabOverviewClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source

