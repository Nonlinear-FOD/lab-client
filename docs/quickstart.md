# Quickstart

New to the lab-client? Follow these steps to get a working setup and run your first calls.

**Note:** Employees (including PhD students) can use wifi via "DTUsecure" or a cable connection. However, student accounts must use ethernet cabled connection.

## 1) Set up your environment
- Prereqs: `git` and Python 3.7+ on your machine.
- Clone `lab-client` somewhere reachable.
  ```bash
  git clone https://github.com/Nonlinear-FOD/lab-client
  ```

- In your experiment folder (where you keep notebooks/scripts), run:
```bash
cd <your-experiment>
python <path-to>/lab-client/tools/setup_venv.py
```
This installs uv, creates `.venv/` with Python 3.12, installs the pinned dependencies, links the clients, and writes `update_venv.py` for later updates.

## 2) Connect to the server
- Hardware server: use `http://<server-ip>:5000` provided by the lab server.
- Docs: when the server is running, docs are hosted at `http://<server-ip>:8000`.

## 3) First login (GitHub device flow)
- On the first secured request you’ll see a URL + code printed automatically. Open the URL, enter the code, approve the OAuth app. Tokens are cached at `~/.remote_lab_auth.json` and refreshed automatically.
- Optional pre-login before creating devices:
```python
from clients.auth_manager import LabAuthManager
LabAuthManager("http://<server-ip>:5000").authorization_header()
```
- Only set `LAB_CLIENT_DISABLE_AUTH=1` when talking to a server that has auth disabled.

## 4) First calls
```python
from clients.osa_clients import OSAClient
from clients.lab_overview_client import LabOverviewClient, LabSystemClient

base = "http://<server-ip>:5000"
user = "alice"

osa = OSAClient(base, "osa_1", span=(1549, 1551), user=user)
osa.sweeptype = "SGL"
osa.sweep()
print(len(osa.wavelengths))

overview = LabOverviewClient(base, user=user)
print(overview.devices())   # connection + lock summary

system = LabSystemClient(base, user=user)
print(system.sessions())    # per-user workers
system.restart_session()    # restart your own worker if needed
```
`user` is sent as `X-User` for lock/session routing; set it to your username.

## 5) Updating your env later
- From your experiment folder:
```bash
python update_venv.py
```
This pulls `lab-client/` and runs `uv pip sync` so removed packages are cleaned up.

## 6) Optional: try the simulated server (no hardware)
If you have the `lab-server` repo locally, you can point clients at the sim for practice:
```bash
cd <path-to>/lab-server/main_server
uv run server_app_fake.py
```
Then use `base = "http://127.0.0.1:5000"` in your client code.

More sample scripts live under `lab-client/examples/`.
