import subprocess
import sys


def main():
    print("Regenerating requirements.runtime.txt from pyproject.toml…")
    subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "-o",
            "requirements.runtime.txt",
            "--upgrade",
        ],
        check=True,
    )
    print("requirements.runtime.txt updated.")


if __name__ == "__main__":
    sys.exit(main())
