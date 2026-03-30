from __future__ import annotations

import sys
from pathlib import Path
from shutil import which


def histogram_command(
    result_file: Path,
    hist_config: Path,
    *,
    result_index: int = 1,
    python_executable: str | Path | None = None,
) -> list[str]:
    """Build the maintained McSAS3 histogram CLI command for the current environment."""

    if result_index < 1:
        raise ValueError("result_index must be >= 1.")

    result_file = Path(result_file)
    hist_config = Path(hist_config)
    histogrammer = which("mcsas3-histogrammer")
    if histogrammer is not None:
        return [histogrammer, "-r", str(result_file), "-H", str(hist_config), "-i", str(result_index)]

    executable = Path(sys.executable if python_executable is None else python_executable).as_posix()
    return [
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
