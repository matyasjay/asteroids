import sys
from pathlib import Path


def runtime_base_path() -> Path:
    """Return the directory that contains bundled runtime assets."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> str:
    return str(runtime_base_path().joinpath(*parts))


def asset_glob(pattern: str) -> str:
    return str(runtime_base_path() / pattern)
