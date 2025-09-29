from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    lab_client_root = Path(__file__).resolve().parent.parent
    if not lab_client_root.is_dir():
        print("Unable to locate lab-client root directory.", file=sys.stderr)
        return 1

    cmd = [
        "uv",
        "run",
        "mkdocs",
        "serve",
        "--dev-addr",
        "0.0.0.0:8000",
    ]

    try:
        subprocess.run(cmd, cwd=lab_client_root, check=True)
    except FileNotFoundError:
        print("`uv` executable not found on PATH.", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
