from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def venv_python(project: Path) -> Path:
    venv = project / ".venv"
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_uv() -> str:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError(
            "`uv` is required. Install it from https://docs.astral.sh/uv/."
        )
    return uv


def main() -> int:
    # Run from the project directory that contains the .venv
    project = Path.cwd()
    py = venv_python(project)
    if not py.exists():
        print(
            f"ERROR: Could not find venv interpreter at {py}.\n"
            "Run setup_venv.py first from your project directory.",
            file=sys.stderr,
        )
        return 2

    # Find the lab-client repo root (this script lives in lab-client/tools/)
    tools_dir = Path(__file__).resolve().parent
    repo_root = tools_dir.parent
    reqs = repo_root / "requirements.runtime.txt"
    if not reqs.exists():
        print(f"ERROR: Missing requirements file at {reqs}", file=sys.stderr)
        return 3

    uv = ensure_uv()

    print(f"Syncing venv packages from {reqs} …")
    # Use sync so removed packages are also uninstalled
    run([uv, "pip", "sync", "-r", str(reqs), "--python", str(py)])

    print("Done. Your venv now matches the pinned requirements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

