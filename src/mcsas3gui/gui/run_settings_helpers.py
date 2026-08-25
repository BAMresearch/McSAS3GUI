from __future__ import annotations

import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

RunConfiguration = dict[str, Any]
_PROGRESS_PATTERN = re.compile(r"chiSqr:\s*(.+?),\s*N accepted:\s*([0-9]+)\s*/\s*([0-9]+)")
_FINAL_PROGRESS_PATTERN = re.compile(r"Final chiSqr:\s*(.+?),\s*N accepted:\s*([0-9]+)")


def combine_run_configuration_documents(yaml_content: object) -> RunConfiguration | None:
    """Merge one or more YAML mapping documents into a single run-configuration mapping."""
    if not yaml_content:
        return None
    if isinstance(yaml_content, Mapping):
        return dict(yaml_content)
    if not isinstance(yaml_content, list):
        raise TypeError("Run configuration content must be a YAML mapping or list of mappings.")

    combined: RunConfiguration = {}
    for document in yaml_content:
        if not isinstance(document, Mapping):
            raise TypeError("One or more YAML documents are not valid configurations.")
        combined.update(document)
    return combined


def preview_result_file_path(temp_dir: Path) -> Path:
    """Return the stable temporary preview result path used by the run-settings preview worker."""
    return temp_dir / "test_data.hdf5"


def cleanup_preview_result_file(result_file: Path | None) -> None:
    """Delete the preview result file if it exists."""
    if result_file is not None and result_file.exists():
        result_file.unlink()


def _format_limit(value: object, *, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, float) and math.isinf(value):
        return "∞"
    return str(value)


def format_preview_status_header(run_config: Mapping[str, Any]) -> str:
    """Build the initial text shown while the preview optimization is running."""
    max_iter = _format_limit(run_config.get("maxIter"), default="default")
    max_accept = _format_limit(run_config.get("maxAccept"), default="∞")
    conv_crit = _format_limit(run_config.get("convCrit"), default="default")
    return (
        "Preview optimization running...\n"
        f"Max Iter: {max_iter}\n"
        f"Max Accept: {max_accept}\n"
        f"Convergence Criterion: {conv_crit}"
    )


def format_preview_progress_message(message: str, *, run_config: Mapping[str, Any] | None) -> str:
    """Format live preview-progress log messages for the run-settings info panel."""
    max_iter = _format_limit(None if run_config is None else run_config.get("maxIter"), default="default")
    max_accept = _format_limit(None if run_config is None else run_config.get("maxAccept"), default="∞")

    progress_match = _PROGRESS_PATTERN.fullmatch(message)
    if progress_match is not None:
        chi_sqr, accepted, attempts = progress_match.groups()
        return f"Reduced chi-square: {chi_sqr} | Accepted: {accepted}/{max_accept} | Attempts: {attempts}/{max_iter}"

    final_match = _FINAL_PROGRESS_PATTERN.fullmatch(message)
    if final_match is not None:
        chi_sqr, accepted = final_match.groups()
        return f"Final reduced chi-square: {chi_sqr} | Accepted: {accepted}/{max_accept}"

    return message
