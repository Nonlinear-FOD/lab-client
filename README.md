# Lab Clients — Quick Setup

Python clients for talking to the Remote Lab server.

## 1) Set up your environment (once per experiment folder)
- Clone this repo (if you don’t already have it):
  ```bash
  git clone https://github.com/Nonlinear-FOD/lab-client
  ```
- In your experiment folder (anywhere you keep notebooks/scripts), run the setup script pointing at this checkout:
  ```bash
  cd <your-experiment>
  python <path-to>/lab-client/tools/setup_venv.py
  ```
  This installs uv, creates `.venv/` with Python 3.12, installs pinned deps, links the clients into the venv, and writes `update_venv.py` for later updates.

## 2) Use in your IDE/REPL
- Most IDEs auto-pick `<your-experiment>/.venv/`; if not:
  - Windows: `<your-experiment>\.venv\Scripts\python.exe`
  - macOS/Linux: `<your-experiment>/.venv/bin/python`

## 3) First calls (device + overview)
```python
from clients.laser_clients import AndoLaserClient
from clients.osa_clients import OSAClient
from clients.lab_overview_client import LabOverviewClient, LabSystemClient

server = "http://<server-ip>:5000"
user = "alice"

laser = AndoLaserClient(server, "ando_laser_1", target_wavelength=1550, power=0, user=user)
osa = OSAClient(server, "osa_1", span=(1545, 1555), user=user)

laser.enable()
osa.sweep()
print("Laser wl:", laser.wavelength)
print("OSA points:", len(osa.wavelengths))

overview = LabOverviewClient(server, user=user)
system = LabSystemClient(server, user=user)
print(overview.devices())       # connection + lock summary
print(system.sessions())        # per-user workers
system.restart_session()        # restart your own worker if it wedges
```

## Authentication (GitHub device flow)
- The first secured request prints a short URL + code; open it, approve the OAuth app, and tokens are cached in `~/.remote_lab_auth.json` (override with `LAB_CLIENT_TOKEN_PATH`). Refresh happens automatically.
- To pre-login:  
  ```python
  from clients.auth_manager import LabAuthManager
  LabAuthManager(server).authorization_header()
  ```
- Set `LAB_CLIENT_DISABLE_AUTH=1` only when talking to legacy servers without auth.

## Updating your environment
- Recommended: from your experiment folder run:
  ```bash
  python update_venv.py
  ```
  This pulls `lab-client/` and runs `uv pip sync` against your `.venv` so removed deps are cleaned up.
- Manual equivalent:
  ```bash
  cd <path-to>/lab-client && git pull --ff-only
  cd <your-experiment>
  uv pip sync -r <path-to>/lab-client/requirements.runtime.txt --python .venv/bin/python
  # Windows:
  # uv pip sync -r <path-to>\lab-client\requirements.runtime.txt --python .venv\Scripts\python.exe
  ```

## Notes
- Code under `lab-client/src/clients/` is picked up immediately via the `.pth` link; restart your REPL if a module was already imported.
- Re-running `tools/setup_venv.py` keeps your existing `.venv`, relinks the clients, and rewrites `update_venv.py`. To also remove stale packages, run `python update_venv.py`.
- The lab-server typically hosts this documentation on port 8000 when running (`http://<server-ip>:8000`).
