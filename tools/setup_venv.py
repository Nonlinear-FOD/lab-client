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


def _supports_uv_pip(uv_exe: str) -> bool:
    try:
        subprocess.run(
            [uv_exe, "pip", "--help"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _persist_uv_path(uv_exe: str) -> None:
    uv_dir = str(Path(uv_exe).parent)
    if os.name == "nt":
        try:
            import winreg  # type: ignore

            # Update user PATH in HKCU\Environment
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ
            )
            try:
                current, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current = ""
            finally:
                winreg.CloseKey(key)

            parts = [p for p in current.split(";") if p]
            if uv_dir not in parts:
                new = (
                    current
                    + (";" if current and not current.endswith(";") else "")
                    + uv_dir
                )
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new)
                winreg.CloseKey(key)
                # Broadcast environment change
                try:
                    import ctypes

                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST,
                        WM_SETTINGCHANGE,
                        0,
                        "Environment",
                        0,
                        5000,
                        ctypes.byref(ctypes.c_ulong()),
                    )
                except Exception:
                    pass
        except Exception:
            # If we cannot persist, we still proceed; current process PATH is augmented
            pass
    else:
        # POSIX: avoid editing shell rc files automatically. Ensure current process PATH
        # includes ~/.local/bin for this run; users can add it permanently if desired.
        pass


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
    if uv and _supports_uv_pip(uv):
        return uv
    print("`uv` not found or `uv pip` unavailable; installing via official installer …")
    install_uv_official()
    # Make sure this process can find it without a restart
    _augment_env_path_for_current_process()
    # Prefer PATH first
    uv = shutil.which("uv")
    if uv and _supports_uv_pip(uv):
        return uv
    # Scan known candidate locations
    for p in _uv_candidate_paths():
        if p.exists() and _supports_uv_pip(str(p)):
            return str(p)
    raise RuntimeError(
        "`uv` installation completed, but a working `uv pip` was not found.\n"
        "Ensure uv is on PATH and is the Astral uv (check `uv --version`)."
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
    # Try to persist uv on PATH for future shells
    _persist_uv_path(uv)

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
    # Install deps using uv pip targeting the venv (no pip fallback)
    run([uv, "pip", "install", "-r", str(reqs), "--python", str(py)])

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

    # 6) Drop a simple project-local updater to pull + sync deps
    updater = project / "update_venv.py"
    try:
        script = f"""
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


def main() -> int:
    project = Path.cwd()
    py = venv_python(project)
    if not py.exists():
        print(f"ERROR: .venv not found at {py}. Run setup_venv.py first.", file=sys.stderr)
        return 2

    repo_root = Path(r"{repo_root}")
    if not repo_root.exists():
        print(f"ERROR: lab-client directory missing at {{repo_root}}", file=sys.stderr)
        return 3

    uv = shutil.which("uv")
    if not uv:
        print("ERROR: `uv` is required. Install from https://docs.astral.sh/uv/", file=sys.stderr)
        return 4

    # 1) Pull latest client code (fast‑forward only)
    print(f"Pulling latest in {{repo_root}} …")
    run(["git", "-C", str(repo_root), "pull", "--ff-only"])

    # 2) Sync venv to pinned requirements
    reqs = repo_root / "requirements.runtime.txt"
    if not reqs.exists():
        print(f"ERROR: Missing requirements file at {{reqs}}", file=sys.stderr)
        return 5
    print(f"Syncing venv packages from {{reqs}} …")
    run([uv, "pip", "sync", "-r", str(reqs), "--python", str(py)])

    print("Done. Clients updated and venv synced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".lstrip()
        updater.write_text(script, encoding="utf-8")
        print(f"Wrote project updater: {updater}")
    except Exception as e:
        print(f"WARNING: Could not write project updater script: {e}")

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
