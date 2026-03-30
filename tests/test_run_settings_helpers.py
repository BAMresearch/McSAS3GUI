from pathlib import Path

import pytest

from mcsas3gui.gui.run_settings_helpers import (
    cleanup_preview_result_file,
    combine_run_configuration_documents,
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
