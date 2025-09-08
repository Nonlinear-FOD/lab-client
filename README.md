# Installation and Setup Guide for Lab Clients in the FOD Lab
These clients are for remote controlling instruments running on Nonlinear-FOD/lab-server using FastAPI.
They provide a clean Python API, e.g.:
```python
from clients.laser_clients import AndoLaserClient
from clients.osa_clients import OSAClient

server = "http://<server-ip>:5000"

# Connect to devices
laser = AndoLaserClient(server, "ando_laser_1", target_wavelength=1550, power=0)
osa = OSAClient(server, "osa_1", span=(1545, 1555))

laser.enable()
osa.sweep()
print("Laser wl:", laser.wavelength)
print("OSA points:", len(osa.wavelengths))
```
# Option A
**Option A (recommended)**

# 0. Make sure uv and git is installed on your pc
`uv` is a modern Python package and environment manager recommended for creating and managing virtual environments.  
We also need `git` to clone the `lab-client` repository.

## Install `git` (Windows)

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win).  
2. Download the installer (64-bit recommended) and run it with default options.  
3. After installation, verify in a new terminal (PowerShell or VS Code terminal):

```powershell
git --version
```
## Install `uv`
`uv` is easily installed with `pip`:
```bash
pip install uv
```
Confirm installation:
```powershell
uv --version
```

# 1. Clone the repository
First, go to any directory you want to have the lab-client repository installed and then clone it to your computer:
```bash
cd <wherever-you-want>
git clone https://github.com/Nonlinear-FOD/lab-client
```
Then create a new branch (so your changes don’t go directly on `main`):
```bash
cd lab-client
git checkout -b my-branch
```

# 2. Create your project directory
Make a directory (or folder) for your experiment wherever you want (separate from the cloned repo) and go to that directory:
```bash
cd my-experiment
```
Do all of the rest of the steps from your `my-experiment` directory.

# 3. Create a virtual environment
Use `uv` to create a fresh environment inside your project:
```bash
uv venv
```
This creates a `.venv/` directory inside `my-experiment/`.

# 4. Link the lab-clients into your venv
Run the helper script from the cloned repo to make the clients importable:
```bash
python <path-to>/lab-client/tools/link_clients.py
```
This writes a `.pth` file into your `.venv` so you can do clean imports like:
```python
from clients.laser_clients import AndoLaserClient
```
NOTE: If your `<path-to>` has spaces, put quotes around it `'<path-to>'`.

# 5. Install dependencies
The repo includes a pinned set of runtime dependencies in `requirements.runtime.txt`.
Install them into your venv:
```bash
uv pip install -r <path-to>/lab-client/requirements.runtime.txt
```

# 6. Verify installation
Check that everything works by running:
```bash
uv run python -c "from clients.osa_clients import OSAClient; print('Import OK')"
```
If you see `Import OK`, you are ready.

# 7. Use in your project
Now you can use the clients in your code or notebooks. For example:
```python
from clients.laser_clients import AndoLaserClient
from clients.osa_clients import OSAClient

server = "http://<server-ip>:5000"

# Connect to devices
laser = AndoLaserClient(server, "ando_laser_1", target_wavelength=1550, power=0)
osa = OSAClient(server, "osa_1", span=(1545, 1555))

laser.enable()
osa.sweep()
print("Laser wl:", laser.wavelength)
print("OSA points:", len(osa.wavelengths))
```
