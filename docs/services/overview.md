# Overview

Read-only endpoints to inspect connected devices and locks, enumerate VISA resources, **and** manage the new per-user session workers (list them, restart your own, or shut them down when a GPIB script wedges).

- Client: `clients.lab_overview_client.LabOverviewClient`

## Quickstart

```python
from clients.lab_overview_client import LabOverviewClient

base = "http://127.0.0.1:5000"
user = "alice"
view = LabOverviewClient(base, user=user)
print(view.devices())                     # connection + lock summary
print(view.sessions())                    # per-user workers with ports + status
view.restart_session()                    # restart your own worker
print(view.list_used_instruments())
print(view.list_connected_instruments())
```

## API Reference

::: clients.lab_overview_client.LabOverviewClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
