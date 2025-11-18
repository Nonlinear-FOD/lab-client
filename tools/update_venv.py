from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HARDCODED_REPO_ROOT = "__REPO_ROOT__"


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

    repo_root = Path(HARDCODED_REPO_ROOT)
    if not repo_root.is_dir():
        print(
            f"ERROR: Configured HARDCODED_REPO_ROOT '{repo_root}' does not exist.",
            file=sys.stderr,
        )
        return 3
    reqs = repo_root / "requirements.runtime.txt"
    if not reqs.exists():
        print(f"ERROR: Missing requirements file at {reqs}", file=sys.stderr)
        return 4

    uv = ensure_uv()

    print(f"Pulling latest changes in {repo_root} …")
    try:
        run(["git", "-C", str(repo_root), "pull", "--ff-only"])
    except subprocess.CalledProcessError as exc:
        print(
            f"WARNING: git pull failed for {repo_root} (exit code {exc.returncode}). "
            "Continuing with local checkout.",
            file=sys.stderr,
        )

    print(f"Syncing venv packages from {reqs} …")
    # Use sync so removed packages are also uninstalled
    run([uv, "pip", "sync", str(reqs), "--python", str(py)])

    print("Done. Your venv now matches the pinned requirements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
