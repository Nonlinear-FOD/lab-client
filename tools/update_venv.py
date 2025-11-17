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


def _determine_repo_root() -> Path:
    """Return the lab-client root directory or instruct the user to set it."""
    if HARDCODED_REPO_ROOT == "__REPO_ROOT__":
        raise RuntimeError(
            "HARDCODED_REPO_ROOT still contains the placeholder path.\n"
            "Edit update_venv.py and set HARDCODED_REPO_ROOT to the absolute "
            "path of your lab-client repo (e.g. /home/user/remote_lab_control/lab-client).",
        )
    root = Path(HARDCODED_REPO_ROOT)
    if not root.is_dir():
        raise RuntimeError(
            f"Configured HARDCODED_REPO_ROOT '{root}' does not exist. "
            "Update the path to point at your lab-client checkout.",
        )
    return root


def _git_pull(repo_root: Path) -> None:
    """Fast-forward the lab-client repo before syncing dependencies."""
    try:
        run(["git", "-C", str(repo_root), "pull", "--ff-only"])
    except subprocess.CalledProcessError as exc:
        print(
            f"WARNING: git pull failed for {repo_root} (exit code {exc.returncode}). "
            "Dependencies will still be synced against the local checkout.",
            file=sys.stderr,
        )


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

    # Resolve the lab-client repo root (hard-coded during setup if available)
    try:
        repo_root = _determine_repo_root()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    reqs = repo_root / "requirements.runtime.txt"
    if not reqs.exists():
        print(f"ERROR: Missing requirements file at {reqs}", file=sys.stderr)
        return 4

    uv = ensure_uv()

    print(f"Pulling latest changes in {repo_root} …")
    _git_pull(repo_root)

    print(f"Syncing venv packages from {reqs} …")
    # Use sync so removed packages are also uninstalled
    run([uv, "pip", "sync", str(reqs), "--python", str(py)])

    print("Done. Your venv now matches the pinned requirements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
