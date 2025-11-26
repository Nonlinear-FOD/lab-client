# Lab Client Documentation

Python client library (`clients.*`) for controlling instruments via the Remote Lab server.

- New here? Start with [Quickstart](quickstart.md).
- Need to manage sessions/locks? See [Services → Overview](services/overview.md) for `LabOverviewClient` and `LabSystemClient`.
- Device-specific guides are under **Devices**; each has Quickstart and common operations.

## Device Configs & Overrides

- Each device on the server has a JSON config keyed by its `device_name` that
  encodes transport details (VISA addresses, COM ports, serial numbers) and safe defaults.
- Typically you only provide `base_url` and `device_name` to a client constructor; addresses/ports come from the server config.
- Passing a non-`None` keyword argument (e.g., `GPIB_address=19`, `com_port=3`, `serial="..."`) overrides the server config for your session.
- Passing `None` leaves the server’s config defaults intact.
