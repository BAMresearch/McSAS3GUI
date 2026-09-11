import logging
from pathlib import Path

import numpy as np
import pandas as pd
from mcsas3 import STAGE_BINNED, prepare_1d_processing_data
from mcsas3.mc_hdf import ResultIndex, storeKV

from mcsas3gui.gui import mcsas3_bridge


def test_processing_frames_from_processing_returns_raw_clipped_and_binned_frames():
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3], dtype=float),
                "I": np.array([10.0, 20.0, 30.0], dtype=float),
                "ISigma": np.array([1.0, 2.0, 3.0], dtype=float),
            }
        ),
        data_range=[0.15, 0.35],
        nbins=1,
    )

    frames = mcsas3_bridge.processing_frames_from_processing(processing)

    assert list(frames.raw.columns) == ["Q", "I", "ISigma"]
    assert len(frames.raw) == 3
    assert len(frames.clipped) == 2
    assert len(frames.binned) == 1
    assert frames.clipped["Q"].tolist() == [0.2, 0.3]


def test_run_test_optimization_uses_canonical_workflow_and_loads_preview(monkeypatch, tmp_path):
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3], dtype=float),
                "I": np.array([10.0, 20.0, 30.0], dtype=float),
                "ISigma": np.array([1.0, 2.0, 3.0], dtype=float),
            }
        ),
        nbins=1,
        analysis_stage=STAGE_BINNED,
    )
    result_file = tmp_path / "preview.h5"
    calls: dict[str, object] = {}

    def fake_optimize(processing_input, target_file: Path, *, result_index: int = 1, **kwargs):
        calls["processing"] = processing_input
        calls["target_file"] = target_file
        calls["result_index"] = result_index
        calls["kwargs"] = kwargs
        repetition_path = ResultIndex(result_index).nxsEntryPoint / "optimization" / "repetition0"
        storeKV(target_file, repetition_path / "modelI", np.array([5.0], dtype=float))
        storeKV(target_file, repetition_path / "acceptedGofs", np.array([2.5, 1.5], dtype=float))
        storeKV(target_file, repetition_path / "acceptedSteps", np.array([0, 4], dtype=int))
        storeKV(target_file, repetition_path / "maxIter", 100)
        storeKV(target_file, repetition_path / "maxAccept", 10)
        storeKV(target_file, repetition_path / "x0", np.array([2.0, 0.5], dtype=float))

    monkeypatch.setattr(mcsas3_bridge, "optimize_processing_data", fake_optimize)

    preview = mcsas3_bridge.run_test_optimization(
        processing,
        result_file,
        {"modelName": "sphere", "nRep": 99},
        result_index=2,
    )

    assert calls["processing"] is processing
    assert calls["target_file"] == result_file
    assert calls["result_index"] == 2
    assert calls["kwargs"]["modelName"] == "sphere"
    assert calls["kwargs"]["nRep"] == 1
    np.testing.assert_allclose(preview.fit_q, np.array([0.2]))
    np.testing.assert_allclose(preview.fit_intensity, np.array([5.0]))
    np.testing.assert_allclose(preview.accepted_gofs, np.array([2.5, 1.5]))
    np.testing.assert_array_equal(preview.accepted_steps, np.array([0, 4]))
    assert preview.max_iter == 100
    assert preview.max_accept == 10
    np.testing.assert_allclose(preview.x0, np.array([2.0, 0.5]))
    assert preview.x0_parameter_names == ("scale", "background")
    np.testing.assert_allclose(preview.fitted_curve, np.array([10.5]))
    np.testing.assert_allclose(preview.background_curve, np.array([0.5]))


def test_load_optimization_preview_reconstructs_porod_enabled_fit(tmp_path):
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3], dtype=float),
                "I": np.array([10.0, 20.0, 30.0], dtype=float),
                "ISigma": np.array([1.0, 2.0, 3.0], dtype=float),
            }
        ),
    )
    result_file = tmp_path / "porod-preview.h5"
    repetition_path = ResultIndex(1).nxsEntryPoint / "optimization" / "repetition0"
    storeKV(result_file, repetition_path / "modelI", np.array([1.0, 2.0, 3.0], dtype=float))
    storeKV(result_file, repetition_path / "acceptedGofs", np.array([1.0], dtype=float))
    storeKV(result_file, repetition_path / "acceptedSteps", np.array([0], dtype=int))
    storeKV(result_file, repetition_path / "maxIter", 100)
    storeKV(result_file, repetition_path / "maxAccept", 10)
    storeKV(result_file, repetition_path / "x0", np.array([2.0, 0.5, 1e-4], dtype=float))
    storeKV(
        result_file,
        repetition_path / "x0ParameterNames",
        ["scale", "background", "porodCoefficient"],
    )

    preview = mcsas3_bridge.load_optimization_preview(result_file, processing)

    assert preview.x0_parameter_names == ("scale", "background", "porodCoefficient")
    np.testing.assert_allclose(
        preview.fitted_curve,
        2.0 * np.array([1.0, 2.0, 3.0]) + 0.5 + 1e-4 * preview.fit_q**-4,
    )
    np.testing.assert_allclose(preview.background_curve, 0.5 + 1e-4 * preview.fit_q**-4)


def test_load_optimization_preview_clips_legacy_infinite_max_accept(tmp_path, caplog):
    processing = prepare_1d_processing_data(
        pd.DataFrame(
            {
                "Q": np.array([0.1, 0.2, 0.3], dtype=float),
                "I": np.array([10.0, 20.0, 30.0], dtype=float),
                "ISigma": np.array([1.0, 2.0, 3.0], dtype=float),
            }
        ),
    )
    result_file = tmp_path / "legacy-infinite-limit-preview.h5"
    repetition_path = ResultIndex(1).nxsEntryPoint / "optimization" / "repetition0"
    storeKV(result_file, repetition_path / "modelI", np.array([1.0, 2.0, 3.0], dtype=float))
    storeKV(result_file, repetition_path / "acceptedGofs", np.array([1.0], dtype=float))
    storeKV(result_file, repetition_path / "acceptedSteps", np.array([0], dtype=int))
    storeKV(result_file, repetition_path / "maxIter", 100)
    storeKV(result_file, repetition_path / "maxAccept", np.inf)
    storeKV(result_file, repetition_path / "x0", np.array([2.0, 0.5], dtype=float))

    with caplog.at_level(logging.WARNING, logger="mcsas3gui.gui.mcsas3_bridge"):
        preview = mcsas3_bridge.load_optimization_preview(result_file, processing)

    assert preview.max_iter == 100
    assert preview.max_accept == 100
    assert "Stored maxAccept is missing or non-finite; using maxIter (100)" in caplog.text
