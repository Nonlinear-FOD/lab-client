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


def _determine_repo_root(project: Path) -> Path:
    """Return the lab-client root directory.

    When this script is templated during setup we drop in an absolute path. If
    that value is still the sentinel, fall back to using this file's location or
    the caller's project tree.
    """
    if HARDCODED_REPO_ROOT != "__REPO_ROOT__":
        root = Path(HARDCODED_REPO_ROOT)
        if root.is_dir():
            return root
    # Best effort: this template normally lives in lab-client/tools/
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent,
        project / "lab-client",
        project.parent / "lab-client",
        here.parent,
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "requirements.runtime.txt").exists():
            return candidate
    raise FileNotFoundError(
        "Unable to determine lab-client root. Set HARDCODED_REPO_ROOT "
        "to an absolute path or place this script inside the repo tree.",
    )


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
        repo_root = _determine_repo_root(project)
    except FileNotFoundError as exc:
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
