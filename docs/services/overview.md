# Overview

Read-only endpoints to inspect connected devices and locks and enumerate VISA resources. Session worker management (list/restart/shutdown) now lives in `LabSystemClient` alongside the maintenance endpoints (`/system/update`, `/client-docs/*`) so the overview client stays focused on visibility.

- Client: `clients.lab_overview_client.LabOverviewClient`
- Maintenance helper: `clients.lab_overview_client.LabSystemClient`

## Quickstart

```python
from clients.lab_overview_client import LabOverviewClient, LabSystemClient

base = "http://127.0.0.1:5000"
user = "alice"
view = LabOverviewClient(base, user=user)
print(view.devices())                     # connection + lock summary
print(view.list_used_instruments())
print(view.list_connected_instruments())

sys = LabSystemClient(base, user=user)
sys.update_server_repo()                      # git pull --ff-only on lab-server
sys.restart_docs()                            # bounce the hosted lab-client docs
print(sys.sessions())                         # per-user workers with ports + status
sys.restart_session()                         # restart your own worker
```

## API Reference

::: clients.lab_overview_client.LabOverviewClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source

## System helper API

::: clients.lab_overview_client.LabSystemClient
    options:
      show_source: false
      show_root_heading: true
      members_order: source
