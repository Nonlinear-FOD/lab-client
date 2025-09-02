import subprocess
import sys
import tempfile
import re
import pathlib


def stripped(path: pathlib.Path) -> list[str]:
    return [l for l in path.read_text().splitlines() if not re.match(r"^\s*#", l)]


def main() -> int:
    cur = pathlib.Path("requirements.runtime.txt")
    if not cur.exists():
        print(
            "requirements.runtime.txt is missing. Regenerate it. By running 'python update_deps.py'",
            file=sys.stderr,
        )
        return 1
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "tmp.txt"
        subprocess.run(
            ["uv", "pip", "compile", "pyproject.toml", "-o", str(tmp), "--upgrade"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if stripped(cur) != stripped(tmp):
            print(
                "requirements.runtime.txt is stale. Re-run update and commit.",
                file=sys.stderr,
            )
            return 1
    print("Deps OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
