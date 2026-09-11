from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_Q_UNITS = "1/nm"
EXPECTED_I_UNITS = "1/(m sr)"

READ_CONFIGURATION_PATHS = [
    REPO_ROOT / "read_configurations/read_nxs_with_omit_QSD.yaml",
    REPO_ROOT / "read_configurations/read_nxs_with_omit_datamerge.yaml",
    REPO_ROOT / "read_configurations/read_roundrobin_3_dat.yaml",
    REPO_ROOT / "read_configurations/read_roundrobin_dat.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/readdata/read_csv_simple.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/readdata/read_many.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/readdata/read_nxs_simple.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/readdata/read_nxs_with_omit.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/readdata/read_pdh.yaml",
]

PREFAB_CONFIGURATION_PATHS = [
    REPO_ROOT / "src/mcsas3gui/configurations/prefab/advanced_nexus_demo.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/prefab/nPSize4_example.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/prefab/round_robin_dataset_1.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/prefab/round_robin_dataset_3.yaml",
]

RUN_CONFIGURATION_PATHS = [
    REPO_ROOT / "run_configurations/run_config_AutoMOF.yaml",
    REPO_ROOT / "run_configurations/run_config_RR_1.yaml",
    REPO_ROOT / "run_configurations/run_config_RR_3.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/run/run_config_sphere_at_hardsphere.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/run/run_config_spheres.yaml",
    REPO_ROOT / "src/mcsas3gui/configurations/run/run_config_spheres_auto.yaml",
]


def _load_yaml_mapping(path: Path) -> dict:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"{path} must contain a YAML mapping"
    return loaded


def _path_id(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


@pytest.mark.parametrize("config_path", READ_CONFIGURATION_PATHS, ids=_path_id)
def test_shipped_read_configurations_declare_source_units(config_path: Path):
    config = _load_yaml_mapping(config_path)

    assert config["QUnits"] == EXPECTED_Q_UNITS
    assert config["IUnits"] == EXPECTED_I_UNITS


@pytest.mark.parametrize("prefab_path", PREFAB_CONFIGURATION_PATHS, ids=_path_id)
def test_prefab_inline_read_configurations_declare_source_units(prefab_path: Path):
    prefab = _load_yaml_mapping(prefab_path)
    read_config = prefab["read_configuration"]

    assert read_config["QUnits"] == EXPECTED_Q_UNITS
    assert read_config["IUnits"] == EXPECTED_I_UNITS


@pytest.mark.parametrize("config_path", RUN_CONFIGURATION_PATHS, ids=_path_id)
def test_shipped_run_configurations_enable_log_random(config_path: Path):
    config = _load_yaml_mapping(config_path)

    assert config["logRandom"] is True
    assert config["fitPorodBackground"] is False


@pytest.mark.parametrize("prefab_path", PREFAB_CONFIGURATION_PATHS, ids=_path_id)
def test_prefab_inline_run_configurations_enable_log_random(prefab_path: Path):
    prefab = _load_yaml_mapping(prefab_path)

    assert prefab["run_configuration"]["logRandom"] is True
    assert prefab["run_configuration"]["fitPorodBackground"] is False
