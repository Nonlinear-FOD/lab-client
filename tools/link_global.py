"""
UNSUPPORTED / QUICK-AND-DIRTY:
Link lab-client into the *user* site-packages (global import) by adding a .pth file.
"""

from __future__ import annotations
import site
import sys
import sysconfig
from pathlib import Path


def main() -> int:
    src = Path(__file__).resolve().parents[1] / "src"
    if not src.exists():
        print(f"ERROR: src path not found: {src}", file=sys.stderr)
        return 2

    try:
        target_dir = Path(site.getusersitepackages())
    except Exception:
        target_dir = Path(sysconfig.get_paths()["purelib"])

    target_dir.mkdir(parents=True, exist_ok=True)
    pth = target_dir / "lab_clients_src.pth"
    pth.write_text(str(src.resolve()) + "\n", encoding="utf-8")

    print("Wrote:", pth)
    print("To uninstall, delete that .pth file.")
    print(
        "Sanity check: python -c \"import clients, sys; print('OK', clients.__file__)\""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
