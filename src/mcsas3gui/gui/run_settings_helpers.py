from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def combine_run_configuration_documents(yaml_content: object) -> dict[str, Any] | None:
    """Merge one or more YAML mapping documents into a single run-configuration mapping."""
    if not yaml_content:
        return None
    if isinstance(yaml_content, Mapping):
        return dict(yaml_content)
    if not isinstance(yaml_content, list):
        raise TypeError("Run configuration content must be a YAML mapping or list of mappings.")

    combined: dict[str, Any] = {}
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
