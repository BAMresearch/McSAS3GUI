from pathlib import Path

import pytest
from matplotlib import pyplot as plt

from mcsas3gui.gui.run_settings_helpers import (
    cleanup_preview_result_file,
    combine_run_configuration_documents,
    format_preview_progress_message,
    format_preview_status_header,
    plot_preview_fit_curves,
    preview_result_file_path,
)


def test_combine_run_configuration_documents_accepts_single_mapping():
    combined = combine_run_configuration_documents({"modelName": "sphere", "nRep": 3})

    assert combined == {"modelName": "sphere", "nRep": 3}


def test_combine_run_configuration_documents_merges_multiple_mappings():
    combined = combine_run_configuration_documents([{"modelName": "sphere"}, {"nRep": 3}])

    assert combined == {"modelName": "sphere", "nRep": 3}


def test_combine_run_configuration_documents_rejects_non_mapping_documents():
    with pytest.raises(TypeError, match="valid configurations"):
        combine_run_configuration_documents([{"modelName": "sphere"}, "bad"])


def test_preview_result_file_path_uses_stable_filename(tmp_path):
    result_file = preview_result_file_path(tmp_path)

    assert result_file == tmp_path / "test_data.hdf5"


def test_cleanup_preview_result_file_removes_existing_file(tmp_path):
    result_file = tmp_path / "test_data.hdf5"
    result_file.write_text("result")

    cleanup_preview_result_file(result_file)

    assert not result_file.exists()


def test_cleanup_preview_result_file_ignores_missing_file(tmp_path):
    cleanup_preview_result_file(Path(tmp_path / "missing.hdf5"))


def test_format_preview_status_header_includes_run_limits():
    header = format_preview_status_header(
        {
            "maxIter": 5000,
            "maxAccept": 125,
            "convCrit": 1.0,
            "fitPorodBackground": True,
        }
    )

    assert "Preview optimization running..." in header
    assert "Max Iter: 5000" in header
    assert "Max Accept: 125" in header
    assert "Convergence Criterion: 1.0" in header
    assert "Non-negative q^-4 Background: enabled" in header


def test_format_preview_status_header_shows_resolved_omitted_limits():
    header = format_preview_status_header({})

    assert "Max Iter: 5000" in header
    assert "Max Accept: 5000" in header


def test_format_preview_status_header_uses_large_max_accept_for_omitted_max_iter():
    header = format_preview_status_header({"maxAccept": 7000})

    assert "Max Iter: 7000" in header
    assert "Max Accept: 7000" in header


def test_plot_preview_fit_curves_adds_grey_dotted_background():
    figure, axes = plt.subplots()

    plot_preview_fit_curves(
        axes,
        fit_q=[0.1, 0.2],
        fitted_intensity=[10.0, 5.0],
        background_intensity=[2.0, 0.5],
    )

    fit_line, background_line = axes.lines
    assert fit_line.get_label() == "Test McSAS3 Optimization"
    assert background_line.get_label() == "Fitted background (flat + Porod)"
    assert background_line.get_color() == "0.5"
    assert background_line.get_linestyle() == ":"
    plt.close(figure)


def test_format_preview_progress_message_formats_live_progress():
    message = format_preview_progress_message(
        "chiSqr: 1.23, N accepted: 4 / 500",
        run_config={"maxIter": 5000, "maxAccept": 125},
    )

    assert message == "Reduced chi-square: 1.23 | Accepted: 4/125 | Attempts: 500/5000"


def test_format_preview_progress_message_formats_final_summary():
    message = format_preview_progress_message(
        "Final chiSqr: 0.98, N accepted: 37",
        run_config={"maxIter": 5000, "maxAccept": 125},
    )

    assert message == "Final reduced chi-square: 0.98 | Accepted: 37/125"
