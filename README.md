# Lab Clients — Quick Setup

These clients provide a clean Python API to control instruments exposed by the lab server (FastAPI).

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

server = "http://<server-ip>:5000"

laser = AndoLaserClient(
    server,
    "ando_laser_1",
    target_wavelength=1550,
    power=0,
    user="<your-name>",
)
osa = OSAClient(
    server,
    "osa_1",
    span=(1545, 1555),
    user="<your-name>",
)

laser.enable()
osa.sweep()
print("Laser wl:", laser.wavelength)
print("OSA points:", len(osa.wavelengths))
```

What the setup script does
- uv install: Installs Astral’s `uv` using the official installer.
  - Windows: runs PowerShell with ExecutionPolicy Bypass and executes `install.ps1`.
  - macOS/Linux: runs `curl -LsSf https://astral.sh/uv/install.sh | sh` (falls back to a Python download if needed).
  - Windows PATH: best‑effort to add the uv bin directory to the user PATH (HKCU\Environment) and broadcast the change.
- Python 3.12 venv: Creates `.venv/` in your experiment folder via `uv venv --python 3.12` (downloads 3.12 if missing).
- Dependencies: Installs pinned runtime deps from `requirements.runtime.txt` into the venv using `uv pip`.
- Client linking: Runs `tools/link_clients.py` to add a `.pth` file into the venv’s site‑packages, so `from clients ...` imports work.
- Import check: Verifies `from clients.osa_clients import OSAClient` with the venv’s Python.

Where things are installed
- uv binary: Typically `~/.local/bin/uv` on macOS/Linux; on Windows under `%USERPROFILE%\AppData\Local\Programs\uv\bin\uv.exe`.
- Project venv: `<your-experiment>/.venv/` (managed by uv, Python 3.12).
- Dependencies: Installed into the project venv.
- Clients link: A `.pth` file is written into the venv’s site‑packages to point at `lab-client/src`.
