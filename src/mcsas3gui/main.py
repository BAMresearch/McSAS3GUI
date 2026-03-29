from __future__ import annotations

from ._bootstrap import ensure_compatible_mcsas3

ensure_compatible_mcsas3()


def main():
    from .__main__ import main as _main

    return _main()


__all__ = ["main"]
