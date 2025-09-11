# Lab Client Documentation

This site documents the Python client library (`clients.*`) for controlling instruments via the Remote Lab server.

- For setup and usage basics, see the repository README.
- Use the navigation to browse device-specific guides and the full API.

## Device Configs & Overrides

- Each device on the server has a JSON config keyed by its `device_name` that
  encodes transport details (e.g., VISA resource, GPIB address/bus, COM port,
  serial number) and safe defaults.
- In typical usage you only provide `base_url` and `device_name` to a client
  constructor. You do not need to pass addresses, ports, or serials.
- If you do pass a non-`None` keyword argument (e.g., `GPIB_address=19`,
  `com_port=3`, `serial="..."`), that value overrides the server config for
  your session.
- Passing `None` leaves the server’s config defaults intact.
