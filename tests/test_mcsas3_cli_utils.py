from pathlib import Path

from mcsas3gui.utils import mcsas3_cli


def test_histogram_command_prefers_installed_entrypoint(monkeypatch):
    monkeypatch.setattr(mcsas3_cli, "which", lambda name: "/tmp/mcsas3-histogrammer" if name == "mcsas3-histogrammer" else None)

    command = mcsas3_cli.histogram_command(Path("result.nxs"), Path("hist.yaml"), result_index=2)

    assert command == ["/tmp/mcsas3-histogrammer", "-r", "result.nxs", "-H", "hist.yaml", "-i", "2"]


def test_histogram_command_falls_back_to_python_module(monkeypatch):
    monkeypatch.setattr(mcsas3_cli, "which", lambda name: None)

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
