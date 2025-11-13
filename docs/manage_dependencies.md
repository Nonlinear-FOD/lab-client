# Dependency Workflow (adding/removing packages)

How to add or remove third‑party packages for the lab-client project and keep downstream experiment environments in sync.

## Why this matters

The `lab-client` repository tracks dependencies in two places:

- `pyproject.toml`/`uv.lock` - canonical source for development installs (used by `uv`).
- `requirements.runtime.txt` - frozen list consumed by the per-experiment virtual environments created via `tools/setup_venv.py`.

Any time you change dependencies, you must update all three so everyone picks up the same versions.

## Step-by-step

**1. Work from the repo root**
```bash
cd lab-client
```
Run the following commands **outside** `.venv`. `uv` needs to see `pyproject.toml`.

**2. Add or remove dependencies**
```bash
# add a package (writes pyproject.toml + uv.lock)
uv add <package-name>

# remove a package
uv remove <package-name>
```

**3. Regenerate the runtime requirements**
```bash
uv run tools/update_deps.py
```
   This script rewrites `requirements.runtime.txt` based on the current lockfile. Commit all changed files (`pyproject.toml`, `uv.lock`, `requirements.runtime.txt`).

**4. Sync your experiment venvs**

   **For this step, you should be in your experiment project folder** and execute:
```bash
python update_venv.py
```
   That script runs `git pull` inside `lab-client/` and `uv pip sync …` against the project’s `.venv`, ensuring removed packages are also uninstalled. Run it whenever dependencies change upstream.

## Tips

- Never edit `requirements.runtime.txt` by hand-always regenerate via `uv run tools/update_deps.py`.
- You can check if `requirements.runtime.txt` is up to date via `uv run tools/check_deps.py`.
- For description of the tools used (uv, venv, git), see `lab-server/main_server/docs/tooling_basics.md`.
