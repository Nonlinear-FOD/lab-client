# Overview Services

Use these helpers to see what’s connected/locked and to manage your own session without touching the server directly. `LabOverviewClient` is read-only; `LabSystemClient` handles restarts and maintenance endpoints.

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
# Admin-only helpers:
# sys.restart_session_for("bob")
# sys.shutdown_session_for("bob")
# sys.disconnect_user_instrument("bob", "osa_1")  # free a single device lock

# Iterating quickly on server code for your own session:
# - Make a change on the server (e.g., add device config/driver).
# - sys.update_server_repo()          # pull the latest server code/config
# - sys.shutdown_session()            # stop your worker
# - Reconnect in your REPL            # a fresh worker loads the new code
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
