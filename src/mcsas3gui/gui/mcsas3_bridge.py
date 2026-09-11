from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import numpy as np
import pandas as pd
from mcsas3 import background_intensity, fit_parameter_names, fitted_intensity
from mcsas3.data_adapters import (
    STAGE_BINNED,
    STAGE_CLIPPED,
    STAGE_RAW,
    fit_arrays_from_bundle,
    frame_from_bundle,
    selected_bundle_from_processing,
)
from mcsas3.data_model import BaseData, DataBundle, ProcessingData
from mcsas3.mc_hdf import ResultIndex, loadKV
from mcsas3.workflows import optimize_processing_data, prepare_1d_processing_data_from_file

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITER = 5000


@dataclass(frozen=True)
class ProcessingFrames1D:
    """Pandas plotting frames for the raw, clipped, and binned 1D processing stages."""

    raw: pd.DataFrame
    clipped: pd.DataFrame
    binned: pd.DataFrame


@dataclass(frozen=True)
class OptimizationPreview1D:
    """Preview-fit arrays and optimizer traces loaded from a single repetition result."""

    fit_q: np.ndarray
    fit_intensity: np.ndarray
    accepted_gofs: np.ndarray
    accepted_steps: np.ndarray
    max_iter: int
    max_accept: int
    x0: np.ndarray
    x0_parameter_names: tuple[str, ...]

    @property
    def fitted_curve(self) -> np.ndarray:
        """Return the complete scale/background-adjusted preview curve."""

        return fitted_intensity(self.fit_intensity, self.x0, self.fit_q)

    @property
    def background_curve(self) -> np.ndarray:
        """Return the fitted flat plus optional Porod background contribution."""

        return background_intensity(self.x0, self.fit_q)


def prepare_processing_from_file(data_file: Path, read_config: Mapping[str, Any]) -> ProcessingData:
    """Prepare canonical 1D processing data for GUI preview and optimization."""

    return prepare_1d_processing_data_from_file(data_file, **dict(read_config))


def processing_frames_from_processing(processing: ProcessingData) -> ProcessingFrames1D:
    """Build 1D plotting frames for the raw, clipped, and binned canonical stages."""

    return ProcessingFrames1D(
        raw=_frame_from_1d_bundle(processing[STAGE_RAW]),
        clipped=_frame_from_1d_bundle(processing[STAGE_CLIPPED]),
        binned=_frame_from_1d_bundle(processing[STAGE_BINNED]),
    )


def run_test_optimization(
    processing: ProcessingData,
    result_file: Path,
    run_config: Mapping[str, Any],
    *,
    result_index: int = 1,
) -> OptimizationPreview1D:
    """Run a single GUI preview optimization and load the resulting preview data."""

    run_kwargs = dict(run_config)
    run_kwargs["nRep"] = 1
    optimize_processing_data(processing, result_file, result_index=result_index, **run_kwargs)
    return load_optimization_preview(result_file, processing, result_index=result_index, repetition=0)


def load_optimization_preview(
    result_file: Path,
    processing: ProcessingData,
    *,
    result_index: int = 1,
    repetition: int = 0,
) -> OptimizationPreview1D:
    """Load preview optimization data for the selected 1D analysis stage."""

    selected_bundle = selected_bundle_from_processing(processing)
    fit_q = _fit_q_from_bundle(selected_bundle)
    repetition_path = _optimization_repetition_path(result_index, repetition)
    x0 = np.asarray(loadKV(result_file, repetition_path / "x0"), dtype=float)
    stored_parameter_names = loadKV(result_file, repetition_path / "x0ParameterNames", default=None)
    if stored_parameter_names is None:
        x0_parameter_names = fit_parameter_names(x0)
    else:
        x0_parameter_names = tuple(
            value.decode() if isinstance(value, (bytes, bytearray, np.bytes_)) else str(value)
            for value in np.asarray(stored_parameter_names).reshape(-1)
        )
    max_iter, max_accept = _preview_limits(
        loadKV(result_file, repetition_path / "maxIter", default=None),
        loadKV(result_file, repetition_path / "maxAccept", default=None),
    )

    return OptimizationPreview1D(
        fit_q=fit_q,
        fit_intensity=np.asarray(loadKV(result_file, repetition_path / "modelI"), dtype=float),
        accepted_gofs=np.asarray(loadKV(result_file, repetition_path / "acceptedGofs"), dtype=float),
        accepted_steps=np.asarray(loadKV(result_file, repetition_path / "acceptedSteps"), dtype=int),
        max_iter=max_iter,
        max_accept=max_accept,
        x0=x0,
        x0_parameter_names=x0_parameter_names,
    )


def _preview_limits(max_iter_value: Any, max_accept_value: Any) -> tuple[int, int]:
    """Return finite limits for current and legacy optimization previews."""

    def finite_limit(value: Any) -> int | None:
        if value is None:
            return None
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(numeric_value) or numeric_value < 0:
            return None
        return math.ceil(numeric_value)

    max_iter = finite_limit(max_iter_value)
    max_accept = finite_limit(max_accept_value)
    if max_iter is None:
        max_iter = max(DEFAULT_MAX_ITER, max_accept or 0)
        logger.warning("Stored maxIter is missing or non-finite; using %d for the preview.", max_iter)
    if max_accept is None:
        max_accept = max_iter
        logger.warning("Stored maxAccept is missing or non-finite; using maxIter (%d) for the preview.", max_accept)
    elif max_accept > max_iter:
        logger.warning("Stored maxAccept exceeds maxIter; clipping it to %d for the preview.", max_iter)
        max_accept = max_iter
    return max_iter, max_accept


def _optimization_repetition_path(result_index: int, repetition: int) -> PurePosixPath:
    """Return the canonical HDF5 path for a stored optimization repetition."""
    return ResultIndex(result_index).nxsEntryPoint / "optimization" / f"repetition{repetition}"


def _fit_q_from_bundle(bundle: DataBundle | Mapping[str, BaseData]) -> np.ndarray:
    """Extract the 1D fit coordinate array from a canonical analysis bundle."""
    q_arrays, _intensity, _sigma = fit_arrays_from_bundle(bundle)
    if len(q_arrays) != 1:
        raise ValueError("GUI optimization preview plotting currently supports only 1D analysis bundles.")
    return q_arrays[0].copy()


def _frame_from_1d_bundle(bundle: DataBundle | Mapping[str, BaseData]) -> pd.DataFrame:
    """Convert a canonical 1D analysis bundle into a plotting dataframe."""
    frame = frame_from_bundle(bundle)
    if "Q" not in frame.columns:
        raise ValueError("GUI plotting currently supports only 1D analysis bundles.")
    return frame
