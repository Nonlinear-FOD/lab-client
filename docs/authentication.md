# Authentication Flow (lab-client)

This guide explains how the lab-client handles GitHub-based authentication. The goals:

- Zero manual setup for typical users—first request triggers a GitHub device login automatically.
- Automatic token persistence + refresh.
- Transparent recovery when tokens expire or the server revokes access.
- Simple escape hatch (`LAB_CLIENT_DISABLE_AUTH=1`) when connecting to legacy servers or when the server has disabled auth entirely.

## Components

### `LabAuthManager` (`clients/auth_manager.py`)

Responsible for the full lifecycle of lab-issued tokens:

| Responsibility | Details |
| --- | --- |
| Token storage | Keeps a per-server entry in `~/.remote_lab_auth.json` (override with `LAB_CLIENT_TOKEN_PATH`). File permissions are tightened to `0600` where possible. |
| Device-flow login | `authorization_header()` starts `/auth/device/start`, prints the verification instructions, and polls `/auth/device/poll` until the server returns access/refresh tokens. |
| Refresh | `_ensure_session()` automatically uses `/auth/token` when the cached access token is stale but the refresh token is still valid. |
| Auto-retry | `reset_session()` drops cached tokens; the next request calls `authorization_header()` again. |

Key methods:

- `authorization_header(force_refresh=False)` → returns `"Bearer …"` header string, optionally forcing a clean login.
- `user_login()` → cached GitHub login name (used when a user didn’t provide `user=` to device clients).
- `reset_session()` → forgets tokens, ensuring the next request performs the device flow.

The CLI messaging the user sees during first login:

```
[remote-lab] Sign in to GitHub to access http://<server>:
  1. Visit https://github.com/login/device
  2. Enter the code: XXXX-XXXX
```

Once the user completes that step, tokens are cached and no further prompts appear until the refresh token expires or is revoked.

### `LabDeviceClient` (`clients/base_client.py`)

Every concrete device client inherits this base. Relevant pieces:

- `__init__`: if `LAB_CLIENT_DISABLE_AUTH` is **not** set and no explicit `LabAuthManager` was provided, the base class instantiates one automatically. It also populates `self.user` from the manager’s cached GitHub login when the caller didn’t pass `user=…`.
- `_headers()`: attaches `Authorization: Bearer …`, `X-User`, and `X-Debug` (when requested).
- `_perform_request()`: centralizes HTTP calls. If the server returns a single 401, it calls `self._auth.reset_session()` and retries once, which triggers a fresh login (`authorization_header()` re-runs the device flow under the hood). Any subsequent 401s bubble up to the caller (e.g., user revoked in GitHub).

This means: **users do not have to import or interact with `LabAuthManager` manually.** First interaction with any client prompts for GitHub approval automatically.

### `LabOverviewClient`

Overview endpoints (`/overview/*`, `/system/resources`) don’t inherit `LabDeviceClient`, so a minimal copy of the same logic lives there: instantiate `LabAuthManager` unless `LAB_CLIENT_DISABLE_AUTH=1`, add the headers, and reuse the same `_perform_request()` retry loop.

## Environment Flags

| Variable | Scope | Effect |
| --- | --- | --- |
| `LAB_CLIENT_TOKEN_PATH` | Client | Override default token cache file. |
| `LAB_CLIENT_DISABLE_AUTH` | Client | When set to `1/true/yes`, skips all auth logic (no `Authorization` header, no device flow). Use when talking to servers that have `LAB_AUTH_DISABLE=1`. |

Set these in the shell **before** launching your Python session. Example (PowerShell):

```powershell
$Env:LAB_CLIENT_DISABLE_AUTH = "1"
uv run ipython
# ... later ...
$Env:LAB_CLIENT_DISABLE_AUTH = $null
```

## Request Flow

1. User instantiates a device client:
   ```python
   from clients.osa_clients import OSAClient
   osa = OSAClient("http://server:5000", "osa_1")
   ```
2. First HTTP request (e.g., during `_initialize_device`):
   - `_perform_request()` builds headers: no token yet, so the server answers 401.
   - Retry branch clears the session, `authorization_header()` kicks off the device flow, the user pastes the GitHub code once, the server returns lab tokens.
   - `_perform_request()` replays the original call with the new Bearer token; the device connects successfully.
3. Later requests reuse the cached token silently. When the server says 401 again (token expired), the retry branch re-authenticates without any manual steps.

If GitHub is unreachable or the user is removed from the org, the second attempt still fails—`requests` raises a runtime error so the user knows to contact an admin.

## Token Store Format

`~/.remote_lab_auth.json` contains a JSON object keyed by base URL:

```json
{
  "http://10.51.33.1:5000": {
    "user": {"login": "alice", "name": "Alice Example", ...},
    "issued_at": 1736360000,
    "access_token": "…",
    "access_token_expires_at": 1739040000,
    "refresh_token": "…",
    "refresh_token_expires_at": 1767890000
  }
}
```

Delete the file (or the entry for a specific server) to force a clean login.

## Troubleshooting

- **401 keeps returning immediately:** User removed from GitHub org/repo; retry will continue to fail until membership is restored.
- **`AuthHttpError: HTTP 404: Not Found` during login:** The server is running without auth (`LAB_AUTH_DISABLE=1`), so disable the client side as well (`LAB_CLIENT_DISABLE_AUTH=1`) or switch to a server that has auth enabled.
- **Need to switch GitHub accounts:** Delete the cache file or run `LabAuthManager.reset_session()`/`$Env:LAB_CLIENT_DISABLE_AUTH=1` temporarily.

With these pieces, every client instance handles authentication transparently, while still giving power users control via env vars when necessary.
