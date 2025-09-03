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
If you are allergic to a proper setup and virtual environments and just want a quick global setup, use **Option B**.
**Not recommended**: This can cause dependency/version conflicts across projects. Prefer Option A for reliability.

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
Do all of the rest of the steps from your my-experiment directory.

# 3. Create a virtual environment
Use `uv` to create a fresh environment inside your project:
```bash
uv venv
```
This creates a `.venv/` directory inside `my-experiment/`.

# 4. Link the lab-clients into your venv
Run the helper script from the cloned repo to make the clients importable:
```bash
python <path-to>//lab-client/tools/link_clients.py
```
This writes a `.pth` file into your `.venv` so you can do clean imports like:
```python
from clients.laser_clients import AndoLaserClient
```

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

# Option B
**Option B - Global link (no venv, not recommended)**
This links the clients into your **user** site-packages with a `.pth` file, so
`from clients...` works from anywhere. No `uv` required.
# 0. Prerequisites
- Git (see installation above)
# 1. Clone
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
# 2. Link the clients globally (user site-packages)
Run the helper script (ships in this repo) to drop a `.pth` file into your user site-packages:
```bash
python /path/to/lab-client/tools/link_global.py
```
You should see it print something like:
```bash
Wrote: C:\Users\YOU\AppData\Roaming\Python\Python3x\site-packages\lab_clients_src.pth
```
# 3. Install runtime dependencies globally (user install)
Use `pip` with `--user` to avoid admin rights and avoid touching system Python:
```bash
python -m pip install --user -r /path/to/lab-client/requirements.runtime.txt
```

# 4. Verify installation
Check that everything works by running:
```bash
uv run python -c "from clients.osa_clients import OSAClient; print('Import OK')"
```
If it prints `Import OK`, you can use the clients from any folder:
```python
from clients.laser_clients import AndoLaserClient
from clients.osa_clients import OSAClient
```
