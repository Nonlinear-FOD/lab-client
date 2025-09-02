from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path


def check(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    # require uv
    if not shutil.which("uv"):
        print(
            "ERROR: `uv` is required. Install from https://docs.astral.sh/uv/.",
            file=sys.stderr,
        )
        return 1

    project = Path.cwd()
    venv = project / ".venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    # ensure project venv exists (use uv only)
    if not py.exists():
        print(f"Creating venv in {venv} via `uv venv` …")
        check(["uv", "venv"])

    # where is lab-clients/src? -> repo_root/src (script is repo_root/tools/link_clients.py)
    src = Path(__file__).resolve().parents[1] / "src"
    if not src.exists():
        print(f"ERROR: cannot find src at {src}", file=sys.stderr)
        return 2

    # ask the venv’s interpreter for its site-packages
    purelib = subprocess.check_output(
        [str(py), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        text=True,
    ).strip()
    sp = Path(purelib)
    sp.mkdir(parents=True, exist_ok=True)

    pth = sp / "lab_clients_src.pth"
    pth.write_text(str(src.resolve()) + "\n", encoding="utf-8")

    # quick import check (uses the venv interpreter)
    # change 'client' if you rename the top-level package dir
    try:
        check([str(py), "-c", "import client; print('Linked OK ->', client.__file__)"])
    except subprocess.CalledProcessError:
        print(
            "WARNING: Could not import `client` in the venv; is your top-level package name correct?",
            file=sys.stderr,
        )

    print("\nDone.")
    print("Use this interpreter in your project:")
    print(f"  {py}")
    print("\nNow you can do:\n  from client.some_client import XClient")
    return 0


if __name__ == "__main__":
    import shutil

    raise SystemExit(main())
