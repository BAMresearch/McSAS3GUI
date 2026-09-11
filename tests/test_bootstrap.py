import sys
from types import SimpleNamespace

import pytest

from mcsas3gui import _bootstrap


def test_has_canonical_mcsas3_requires_histogram_cli_module(monkeypatch):
    monkeypatch.setattr(
        _bootstrap.importlib.util,
        "find_spec",
        lambda module_name: None if module_name == "mcsas3.mcsas3_cli_histogrammer" else object(),
    )

    assert _bootstrap._has_canonical_mcsas3() is False


def test_has_canonical_mcsas3_requires_fitted_background_api(monkeypatch):
    monkeypatch.setattr(_bootstrap.importlib.util, "find_spec", lambda module_name: object())
    monkeypatch.setattr(
        _bootstrap.importlib,
        "import_module",
        lambda module_name: SimpleNamespace(background_intensity=lambda: None),
    )

    assert _bootstrap._has_canonical_mcsas3() is False


def test_has_canonical_mcsas3_accepts_complete_fitted_background_api(monkeypatch):
    monkeypatch.setattr(_bootstrap.importlib.util, "find_spec", lambda module_name: object())
    monkeypatch.setattr(
        _bootstrap.importlib,
        "import_module",
        lambda module_name: SimpleNamespace(
            background_intensity=lambda: None,
            fit_parameter_names=lambda: None,
            fitted_intensity=lambda: None,
        ),
    )

    assert _bootstrap._has_canonical_mcsas3() is True


def test_ensure_compatible_mcsas3_returns_none_when_api_is_available(monkeypatch):
    monkeypatch.setattr(_bootstrap, "_has_canonical_mcsas3", lambda: True)

    assert _bootstrap.ensure_compatible_mcsas3() is None


def test_ensure_compatible_mcsas3_uses_candidate_source_path(monkeypatch, tmp_path):
    state = iter([False, True])
    monkeypatch.setattr(_bootstrap, "_has_canonical_mcsas3", lambda: next(state))
    monkeypatch.setattr(_bootstrap, "_candidate_mcsas3_src_paths", lambda: [tmp_path])
    monkeypatch.setattr(_bootstrap, "_clear_imported_mcsas3_modules", lambda: None)
    monkeypatch.setattr(_bootstrap.importlib, "invalidate_caches", lambda: None)
    monkeypatch.setattr(sys, "path", list(sys.path))

    selected = _bootstrap.ensure_compatible_mcsas3()

    assert selected == tmp_path
    assert sys.path[0] == str(tmp_path)


def test_ensure_compatible_mcsas3_raises_when_no_compatible_source_exists(monkeypatch):
    monkeypatch.setattr(_bootstrap, "_has_canonical_mcsas3", lambda: False)
    monkeypatch.setattr(_bootstrap, "_candidate_mcsas3_src_paths", lambda: [])

    with pytest.raises(ImportError, match="canonical workflow and fitted-background APIs"):
        _bootstrap.ensure_compatible_mcsas3()
