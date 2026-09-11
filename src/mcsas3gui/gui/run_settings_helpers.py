from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
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


def _resolved_run_limits(run_config: Mapping[str, Any] | None) -> tuple[int, int]:
    """Mirror the core's finite stopping-limit defaults for GUI status text."""

    config = {} if run_config is None else run_config

    def finite_limit(value: object) -> int | None:
        if value is None:
            return None
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(numeric_value) or numeric_value < 0:
            return None
        return math.ceil(numeric_value)

    max_accept = finite_limit(config.get("maxAccept"))
    max_iter = finite_limit(config.get("maxIter"))
    if max_iter is None:
        max_iter = max(5000, max_accept or 0)
    if max_accept is None or max_accept > max_iter:
        max_accept = max_iter
    return max_iter, max_accept


def configured_model_parameter_value(
    parameter: str,
    default_value: Any,
    run_config: Mapping[str, Any],
) -> str:
    """Format a SasModels parameter using configured values before raw defaults."""

    fit_limits = run_config.get("fitParameterLimits")
    if isinstance(fit_limits, Mapping) and parameter in fit_limits:
        return f"{fit_limits[parameter]} (fit range)"
    static_parameters = run_config.get("staticParameters")
    if isinstance(static_parameters, Mapping) and parameter in static_parameters:
        return f"{static_parameters[parameter]} (static)"
    return f"{default_value} (SasModels default)"


def format_preview_status_header(run_config: Mapping[str, Any]) -> str:
    """Build the initial text shown while the preview optimization is running."""
    max_iter, max_accept = _resolved_run_limits(run_config)
    conv_crit = _format_limit(run_config.get("convCrit"), default="default")
    flat_background_mode = run_config.get("fitFlatBackground", True)
    porod_status = "enabled" if run_config.get("fitPorodBackground", False) else "disabled"
    return (
        "Preview optimization running...\n"
        f"Max Iter: {max_iter}\n"
        f"Max Accept: {max_accept}\n"
        f"Convergence Criterion: {conv_crit}\n"
        f"Flat Background Fit: {flat_background_mode}\n"
        f"Non-negative q^-4 Background: {porod_status}"
    )


def plot_preview_fit_curves(
    axes: Any,
    fit_q: Sequence[float],
    fitted_intensity: Sequence[float],
    background_intensity: Sequence[float],
) -> None:
    """Plot the complete preview fit and its fitted background contribution."""

    axes.plot(fit_q, fitted_intensity, "r--", label="Test McSAS3 Optimization", zorder=10)
    axes.plot(
        fit_q,
        background_intensity,
        color="0.5",
        linestyle=":",
        label="Fitted background (flat + Porod)",
        zorder=9,
    )


def format_preview_progress_message(message: str, *, run_config: Mapping[str, Any] | None) -> str:
    """Format live preview-progress log messages for the run-settings info panel."""
    max_iter, max_accept = _resolved_run_limits(run_config)

    progress_match = _PROGRESS_PATTERN.fullmatch(message)
    if progress_match is not None:
        chi_sqr, accepted, attempts = progress_match.groups()
        return f"Reduced chi-square: {chi_sqr} | Accepted: {accepted}/{max_accept} | Attempts: {attempts}/{max_iter}"

    final_match = _FINAL_PROGRESS_PATTERN.fullmatch(message)
    if final_match is not None:
        chi_sqr, accepted = final_match.groups()
        return f"Final reduced chi-square: {chi_sqr} | Accepted: {accepted}/{max_accept}"

    return message
