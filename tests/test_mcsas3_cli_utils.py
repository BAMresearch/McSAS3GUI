from pathlib import Path

from mcsas3gui.utils import mcsas3_cli


def test_histogram_subprocess_prefers_sibling_source_checkout(monkeypatch, tmp_path):
    source_root = tmp_path / "McSAS3" / "src"
    source_root.mkdir(parents=True)
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.setattr(mcsas3_cli, "_compatible_source_checkout", lambda: source_root)
    monkeypatch.setattr(
        mcsas3_cli,
        "which",
        lambda name: "/tmp/mcsas3-histogrammer" if name == "mcsas3-histogrammer" else None,
    )

    command_spec = mcsas3_cli.histogram_subprocess_spec(
        Path("result.nxs"),
        Path("hist.yaml"),
        result_index=2,
        python_executable="/tmp/python",
    )

    assert command_spec.args == [
        "/tmp/python",
        "-m",
        "mcsas3.mcsas3_cli_histogrammer",
        "-r",
        "result.nxs",
        "-H",
        "hist.yaml",
        "-i",
        "2",
    ]
    assert command_spec.env_overrides == {"PYTHONPATH": source_root.as_posix()}


def test_histogram_subprocess_prefers_bundled_helper_when_frozen(monkeypatch, tmp_path):
    bundle_root = tmp_path / "bundle"
    helper_name = mcsas3_cli._histogrammer_executable_name()
    helper_path = bundle_root / "helpers" / "mcsas3-histogrammer" / helper_name
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text("")
    helper_path.chmod(0o755)

    monkeypatch.setattr(mcsas3_cli, "_compatible_source_checkout", lambda: None)
    monkeypatch.setattr(mcsas3_cli, "which", lambda name: "/tmp/mcsas3-histogrammer")
    monkeypatch.setattr(mcsas3_cli.sys, "frozen", True, raising=False)
    monkeypatch.setattr(mcsas3_cli.sys, "executable", str(bundle_root / "McSAS3GUI"))

    command_spec = mcsas3_cli.histogram_subprocess_spec(Path("result.nxs"), Path("hist.yaml"), result_index=1)

    assert command_spec.args == [
        helper_path.as_posix(),
        "-r",
        "result.nxs",
        "-H",
        "hist.yaml",
        "-i",
        "1",
    ]
    assert command_spec.env_overrides is None


def test_histogram_command_prefers_installed_entrypoint(monkeypatch):
    monkeypatch.setattr(mcsas3_cli, "_compatible_source_checkout", lambda: None)
    monkeypatch.setattr(mcsas3_cli, "_adjacent_histogrammer", lambda executable: None)
    monkeypatch.setattr(
        mcsas3_cli,
        "which",
        lambda name: "/tmp/mcsas3-histogrammer" if name == "mcsas3-histogrammer" else None,
    )
    monkeypatch.delattr(mcsas3_cli.sys, "frozen", raising=False)

    command = mcsas3_cli.histogram_command(Path("result.nxs"), Path("hist.yaml"), result_index=2)

    assert command == ["/tmp/mcsas3-histogrammer", "-r", "result.nxs", "-H", "hist.yaml", "-i", "2"]


def test_histogram_command_falls_back_to_python_module(monkeypatch):
    monkeypatch.setattr(mcsas3_cli, "_compatible_source_checkout", lambda: None)
    monkeypatch.setattr(mcsas3_cli, "_adjacent_histogrammer", lambda executable: None)
    monkeypatch.setattr(mcsas3_cli, "which", lambda name: None)
    monkeypatch.delattr(mcsas3_cli.sys, "frozen", raising=False)

    command = mcsas3_cli.histogram_command(
        Path("result.nxs"),
        Path("hist.yaml"),
        result_index=3,
        python_executable="/tmp/python",
    )

    assert command == [
        "/tmp/python",
        "-m",
        "mcsas3.mcsas3_cli_histogrammer",
        "-r",
        "result.nxs",
        "-H",
        "hist.yaml",
        "-i",
        "3",
    ]


def test_histogram_command_prefers_entrypoint_beside_selected_python(monkeypatch, tmp_path):
    bin_dir = tmp_path / "venv" / ("Scripts" if mcsas3_cli.os.name == "nt" else "bin")
    bin_dir.mkdir(parents=True)
    python_executable = bin_dir / ("python.exe" if mcsas3_cli.os.name == "nt" else "python3.13")
    histogrammer = bin_dir / mcsas3_cli._histogrammer_executable_name()
    python_executable.write_text("")
    histogrammer.write_text("")
    monkeypatch.setattr(mcsas3_cli, "_compatible_source_checkout", lambda: None)
    monkeypatch.setattr(mcsas3_cli, "which", lambda name: "/wrong-environment/mcsas3-histogrammer")
    monkeypatch.delattr(mcsas3_cli.sys, "frozen", raising=False)

    command = mcsas3_cli.histogram_command(
        Path("result.nxs"),
        Path("hist.yaml"),
        result_index=1,
        python_executable=python_executable,
    )

    assert command == [
        histogrammer.as_posix(),
        "-r",
        "result.nxs",
        "-H",
        "hist.yaml",
        "-i",
        "1",
    ]
