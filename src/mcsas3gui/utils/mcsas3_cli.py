from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from .. import _bootstrap


@dataclass(frozen=True)
class SubprocessSpec:
    """Subprocess argument list plus optional environment overrides."""

    args: list[str]
    env_overrides: dict[str, str] | None = None

    def merged_env(self) -> dict[str, str] | None:
        """Return a copy of the current environment with any overrides applied."""
        if not self.env_overrides:
            return None
        env = os.environ.copy()
        env.update(self.env_overrides)
        return env


def _compatible_source_checkout() -> Path | None:
    """Return the sibling McSAS3 source root when available in a dev checkout."""
    for candidate in _bootstrap._candidate_mcsas3_src_paths():
        if candidate.is_dir():
            return candidate
    return None


def _pythonpath_override(source_root: Path) -> dict[str, str]:
    """Build the `PYTHONPATH` override needed for subprocesses to import the sibling core repo."""
    current = os.environ.get("PYTHONPATH")
    source_value = source_root.as_posix()
    if not current:
        return {"PYTHONPATH": source_value}
    return {"PYTHONPATH": f"{source_value}{os.pathsep}{current}"}


def histogram_subprocess_spec(
    result_file: Path,
    hist_config: Path,
    *,
    result_index: int = 1,
    python_executable: str | Path | None = None,
) -> SubprocessSpec:
    """Build the maintained histogram subprocess invocation for the current environment.

    In a sibling-checkout development setup, prefer the local `McSAS3/src` tree over the installed
    `mcsas3` package so the GUI and direct imports execute against the same core code.
    """

    if result_index < 1:
        raise ValueError("result_index must be >= 1.")

    result_file = Path(result_file)
    hist_config = Path(hist_config)
    executable = Path(sys.executable if python_executable is None else python_executable).as_posix()
    module_command = [
        executable,
        "-m",
        "mcsas3.mcsas3_cli_histogrammer",
        "-r",
        str(result_file),
        "-H",
        str(hist_config),
        "-i",
        str(result_index),
    ]

    source_root = _compatible_source_checkout()
    if source_root is not None:
        return SubprocessSpec(module_command, env_overrides=_pythonpath_override(source_root))

    histogrammer = which("mcsas3-histogrammer")
    if histogrammer is not None:
        return SubprocessSpec([histogrammer, "-r", str(result_file), "-H", str(hist_config), "-i", str(result_index)])

    return SubprocessSpec(module_command)


def histogram_command(
    result_file: Path,
    hist_config: Path,
    *,
    result_index: int = 1,
    python_executable: str | Path | None = None,
) -> list[str]:
    """Build only the histogram subprocess argument list for the current environment."""
    return histogram_subprocess_spec(
        result_file,
        hist_config,
        result_index=result_index,
        python_executable=python_executable,
    ).args
