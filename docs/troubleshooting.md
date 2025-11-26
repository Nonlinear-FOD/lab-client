# Troubleshooting (clients)

Common issues and quick fixes.

- **401 Unauthorized right away**
  - You haven’t logged in yet or the server has auth disabled while the client expects it. Follow the device-code prompt, or set `LAB_CLIENT_DISABLE_AUTH=1` only if the server runs with `LAB_AUTH_DISABLE=1`.
- **401 keeps repeating after login**
  - Token expired or GitHub membership revoked. Delete `~/.remote_lab_auth.json` (or your custom `LAB_CLIENT_TOKEN_PATH`) and retry; ensure you’re in the allowed org/repo.
- **422 Missing init params**
  - Pass required constructor args (e.g., `span` for OSA) or check for typos.
- **404 / 405 on an endpoint**
  - The property/method isn’t allow-listed on the server. Verify the device config and that you’re using the right HTTP verb (methods are POST, properties are GET/POST with `value`).
- **Connection errors / timeouts**
  - Check `base_url` and that the server is reachable (port 5000). If using the fake server, skip endpoints that probe hardware (e.g., `/system/resources`).
- **Need a clean auth/login switch**
  - Delete the token file or call `LabAuthManager(base).reset_session()`, then retry to trigger a fresh device flow.
