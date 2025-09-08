from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

# Target Python version for the experiment environments
TARGET_PYTHON = "3.12"


def run(cmd: list[str], cwd: str | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd)


## Removed pip-based uv discovery to enforce PATH-installed uv


def _uv_candidate_paths() -> list[Path]:
    home = Path.home()
    candidates: list[Path] = []
    if os.name == "nt":
        # Common locations for installer/user installs
        candidates.append(home / ".local" / "bin" / "uv.exe")
        candidates.append(home / ".local" / "bin" / "uv")
        candidates.append(
            home / "AppData" / "Local" / "Programs" / "uv" / "bin" / "uv.exe"
        )
        candidates.append(home / "AppData" / "Local" / "Programs" / "uv" / "bin" / "uv")
        candidates.append(
            home / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "uv.exe"
        )
    else:
        # POSIX default installer location
        candidates.append(home / ".local" / "bin" / "uv")
        candidates.append(Path("/usr/local/bin/uv"))
        candidates.append(Path("/opt/homebrew/bin/uv"))  # Apple Silicon brew
        candidates.append(Path("/usr/bin/uv"))
    return candidates


def _augment_env_path_for_current_process() -> None:
    # Ensure typical install dirs are visible for this process
    paths = [str(p.parent) for p in _uv_candidate_paths()]
    cur = os.environ.get("PATH", "")
    extras = [p for p in paths if p and p not in cur]
    if extras:
        os.environ["PATH"] = (
            os.pathsep.join(extras + [cur]) if cur else os.pathsep.join(extras)
        )


def find_uv() -> str | None:
    # Try PATH first
    uv = shutil.which("uv")
    if uv:
        return uv
    # Try common install locations and temporarily add them to PATH
    for p in _uv_candidate_paths():
        if p.exists():
            _augment_env_path_for_current_process()
            return str(p)
    return None


def install_uv_official() -> None:
    if os.name == "nt":
        # Use PowerShell with ExecutionPolicy Bypass to run the official installer
        ps = (
            shutil.which("powershell")
            or shutil.which("powershell.exe")
            or shutil.which("pwsh")
        )
        if not ps:
            raise RuntimeError("PowerShell not found to run uv installer.")
        cmd = [
            ps,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "irm https://astral.sh/uv/install.ps1 | iex",
        ]
        run(cmd)
    else:
        # Prefer curl | sh; fallback to urllib + sh
        curl = shutil.which("curl")
        if curl:
            run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
        else:
            print("Downloading uv installer via Python …")
            with urlopen("https://astral.sh/uv/install.sh") as resp:
                script = resp.read()
            proc = subprocess.run(["sh"], input=script, check=True)


def ensure_uv() -> str:
    uv = find_uv()
    if uv:
        return uv
    print("`uv` not found; installing via official installer …")
    install_uv_official()
    # Make sure this process can find it without a restart
    _augment_env_path_for_current_process()
    uv = find_uv()
    if uv:
        return uv
    raise RuntimeError(
        "`uv` installation completed, but the executable was not found.\n"
        "Ensure that your shell PATH includes the uv install directory (e.g. ~/.local/bin on POSIX)."
    )


def venv_python(project: Path) -> Path:
    venv = project / ".venv"
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def main() -> int:
    project = Path.cwd()
    repo_tools = Path(__file__).resolve().parent
    repo_root = repo_tools.parent

    print(f"Project directory: {project}")
    print(f"Repository root:  {repo_root}")

    # 1) Ensure uv is present
    uv = ensure_uv()
    print(f"Using uv: {uv}")

    # 2) Create venv if missing
    py = venv_python(project)
    if not py.exists():
        print(f"Creating virtual environment with `uv venv --python {TARGET_PYTHON}` …")
        # This will download/install the requested Python if necessary
        run([uv, "venv", "--python", TARGET_PYTHON])  # creates .venv in CWD
    else:
        print("Virtual environment already exists.")
        # Check interpreter version and warn if it doesn't match the target
        try:
            out = subprocess.check_output(
                [
                    str(py),
                    "-c",
                    "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')",
                ],
                text=True,
            ).strip()
            if out != TARGET_PYTHON:
                print(
                    f"WARNING: .venv uses Python {out}, but target is {TARGET_PYTHON}.\n"
                    "         If you want to switch, remove `.venv/` and re-run this script."
                )
        except Exception:
            pass

    # 3) Install runtime dependencies into the venv
    reqs = repo_root / "requirements.runtime.txt"
    if not reqs.exists():
        raise FileNotFoundError(f"Missing requirements file: {reqs}")
    print(f"Installing dependencies from {reqs} …")
    # Prefer uv pip into the specific venv. Fallback to ensurepip + pip.
    try:
        run([uv, "pip", "install", "-r", str(reqs), "--python", str(py)])
    except subprocess.CalledProcessError:
        print("`uv pip` failed or pip missing in venv; bootstrapping pip …")
        run([str(py), "-m", "ensurepip", "--upgrade"])  # ensure pip in venv
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"])  # modern pip
        run([str(py), "-m", "pip", "install", "-r", str(reqs)])

    # 4) Link the clients into this venv
    link_script = repo_tools / "link_clients.py"
    if not link_script.exists():
        raise FileNotFoundError(f"Missing link script: {link_script}")
    print("Linking clients into the venv …")
    run([sys.executable, str(link_script)])

    # 5) Verify import using the venv interpreter
    print("Verifying imports …")
    run(
        [
            str(py),
            "-c",
            (
                "from clients.osa_clients import OSAClient; "
                "print('Import OK:', OSAClient)"
            ),
        ]
    )

    print("\nSetup complete. To use this environment:")
    print(f"  Interpreter: {py}")
    print("  Example (with uv): uv run ipython")
    print("  Fallback:          .venv/bin/python -m ipython")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        cmd = getattr(e, "cmd", None)
        print(f"Command failed: {cmd}", file=sys.stderr)
        raise
