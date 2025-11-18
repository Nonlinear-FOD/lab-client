# Lab Clients — Quick Setup

These clients provide a clean Python API to control instruments exposed by the lab server (FastAPI).

Prerequisite: Install `git` (Windows)

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win).  
2. Download the installer and run it with default options.  

Quick start

- Clone the repo somewhere convenient:

  ```bash
  cd <wherever-you-want>
  git clone https://github.com/Nonlinear-FOD/lab-client
  ```

- Create (or open) your experiment folder and run the installer from there:

  ```bash
  cd <your-experiment>
  python <path-to>/lab-client/tools/setup_venv.py
  ```

Use in your IDE
- If you open/run your IDE in `<your-experiment>`, most IDEs auto-detect `.venv/` and use it automatically.
- Note: If that doesn’t happen, manually select the interpreter:
  - Windows: `<your-experiment>\.venv\Scripts\python.exe`
  - macOS/Linux: `<your-experiment>/.venv/bin/python`

Example usage
```python
from clients.laser_clients import AndoLaserClient
from clients.osa_clients import OSAClient
from clients.lab_overview_client import LabOverviewClient, LabSystemClient

server = "http://<server-ip>:5000"
user = "alice"
laser = AndoLaserClient(
    server,
    "ando_laser_1",
    target_wavelength=1550,
    power=0,
    user=user,
)
osa = OSAClient(
    server,
    "osa_1",
    span=(1545, 1555),
    user=user,
)

laser.enable()
osa.sweep()
print("Laser wl:", laser.wavelength)
print("OSA points:", len(osa.wavelengths))

overview = LabOverviewClient(server, user=user)
print(overview.sessions())      # see per-user workers
overview.restart_session()      # restart your own worker if it wedges

system = LabSystemClient(server, user=user)
system.docs_status()            # check if hosted docs are running
```

Authentication & token storage
------------------------------

The first request to a secured lab server now triggers a GitHub device-code login. The client prints a short URL + code; open it, authorize the GitHub OAuth app, and the client will cache tokens under `~/.remote_lab_auth.json` (override with `LAB_CLIENT_TOKEN_PATH`). Future sessions reuse those tokens and silently refresh them until the refresh token expires.

- Nothing special is required in your code—instantiating any device client will automatically prompt when the server demands auth.
- To pre-login (e.g., before creating devices) run:

  ```python
  from clients.auth_manager import LabAuthManager
  LabAuthManager("http://127.0.0.1:5000").authorization_header()
  ```

- Set `LAB_CLIENT_DISABLE_AUTH=1` only when talking to legacy servers without the auth layer; otherwise requests will fail with `401 Unauthorized`.

What the setup script does
- uv install: Installs Astral’s `uv` using the official installer.
  - Windows: runs PowerShell with ExecutionPolicy Bypass and executes `install.ps1`.
  - macOS/Linux: runs `curl -LsSf https://astral.sh/uv/install.sh | sh` (falls back to a Python download if needed).
  - Windows PATH: best‑effort to add the uv bin directory to the user PATH (HKCU\Environment) and broadcast the change.
- Python 3.12 venv: Creates `.venv/` in your experiment folder via `uv venv --python 3.12` (downloads 3.12 if missing).
- Dependencies: Installs pinned runtime deps from `requirements.runtime.txt` into the venv using `uv pip`.
- Client linking: Runs `tools/link_clients.py` to add a `.pth` file into the venv’s site‑packages, so `from clients ...` imports work.
- Import check: Verifies `from clients.osa_clients import OSAClient` with the venv’s Python.
- Project updater: Writes `<your-experiment>/update_venv.py`, a helper that runs `git pull` in `lab-client/` and `uv pip sync` against your `.venv` so removed packages are also uninstalled.

Where things are installed
- uv binary: Typically `~/.local/bin/uv` on macOS/Linux; on Windows under `%USERPROFILE%\AppData\Local\Programs\uv\bin\uv.exe`.
- Project venv: `<your-experiment>/.venv/` (managed by uv, Python 3.12).
- Dependencies: Installed into the project venv.
- Clients link: A `.pth` file is written into the venv’s site‑packages to point at `lab-client/src`.

Update an existing setup
- Quick path (recommended): from your project directory, run the updater that setup created:

  ```bash
  cd <your-experiment>
  python update_venv.py
  ```

  This will:
  - `git pull --ff-only` inside your `lab-client/` checkout
  - `uv pip sync -r lab-client/requirements.runtime.txt --python .venv/bin/python`

- Manual path (equivalent steps):

  ```bash
  # 1) Update the client repo
  cd <path-to>/lab-client
  git pull --ff-only

  # 2) Sync your project venv
  cd <your-experiment>
  # macOS/Linux
  uv pip sync -r <path-to>/lab-client/requirements.runtime.txt --python .venv/bin/python
  # Windows
  uv pip sync -r <path-to>\lab-client\requirements.runtime.txt --python .venv\Scripts\python.exe
  ```

Notes
- Code changes under `lab-client/src/clients/` are picked up immediately thanks to the `.pth` link; restart your REPL if a module was already imported.
- Re-running `setup_venv.py` in an existing project:
  - Detects `.venv` and leaves it in place.
  - Runs `uv pip install -r …` (adds/updates deps but does not remove stale ones).
  - Re-links clients and (re)writes `update_venv.py`.
  - If you want to also remove packages that are no longer needed, prefer `python update_venv.py` or `uv pip sync` directly.
